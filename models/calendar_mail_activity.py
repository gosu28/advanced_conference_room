import datetime
from datetime import date,timedelta

from odoo import api, models
from odoo.http import request


class CalendarMailActivity(models.Model):
    _name = 'calendar.event'
    _inherit = ['calendar.event', 'mail.thread', 'mail.activity.mixin']

    @api.model
    def create(self, values):
        if values.get('create_by_duplicate') == False:
            res = super(CalendarMailActivity, self).create(values)
            partner_ids = []
            state = ['accepted', 'declined']
            attendee_ids = res.env['calendar.attendee'].sudo().search([('event_id', '=', res.id)])
            for attendee_id in attendee_ids:
                if attendee_id.state not in state:
                    partner_ids.append(attendee_id.partner_id.id)
            user_ids = res.env['res.users'].sudo().search([('partner_id', '=', partner_ids)])
            for user_id in user_ids:
                res.activity_schedule('advanced_conference_room.mail_act_meeting', date_deadline=date.today(),
                                      user_id=user_id.id, automated=True, calendar_event_id=res.id)
            return res
        else:
            res = super(CalendarMailActivity, self).create(values)
            return res


    def write(self, values):
        # self.ensure_one()
        for rec in self:
            if values.get('partner_ids'):
                state = ['accepted', 'declined']
                old_user_ids = [e.user_id.id for e in rec.env['mail.activity'].sudo().search(
                    [('res_id', '=', rec.id), ('res_model', '=', 'calendar.event')])]
                new_user_ids = [e.id for e in rec.env['res.users'].sudo().search(
                    [('partner_id', '=', values.get('partner_ids')[0][-1])])]
                user_ids = old_user_ids + new_user_ids
                users = rec.env['res.users'].sudo().search([('id', '=', user_ids)])
                for user_id in users:
                    attendee_id = rec.env['calendar.attendee'].sudo().search(
                        [('event_id', '=', rec.id), ('partner_id', '=', user_id.partner_id.id)])
                    if attendee_id:
                        if attendee_id.state not in state:
                            if user_id.id in new_user_ids and user_id.id not in old_user_ids:
                                rec.activity_schedule('advanced_conference_room.mail_act_meeting',
                                                      date_deadline=date.today(),
                                                      user_id=user_id.id, automated=True)
                            if user_id.id in old_user_ids and user_id.id not in new_user_ids:
                                rec.env['mail.activity'].sudo().search(
                                    [('res_id', '=', rec.id), ('res_model', '=', 'calendar.event'),
                                     ('user_id', '=', user_id.id)]).unlink()
                    else:
                        rec.activity_schedule('advanced_conference_room.mail_act_meeting', date_deadline=date.today(),
                                              user_id=user_id.id, automated=True, calendar_event_id=rec.id)
        return super(CalendarMailActivity, self).write(values)

    def unlink(self):
        for rec in self:
            rec.env['mail.activity'].sudo().search(
                [('res_id', '=', rec.id), ('res_model', '=', 'calendar.event')]).unlink()
            odoobot = self.env['res.partner'].sudo().search([('id', '=', 3), ('active', '=', False)])
            ch_obj = self.env['mail.channel']
            for partner in rec.partner_ids:
                ch = ch_obj.sudo().search([('channel_partner_ids', 'in', partner.id),
                                           ('channel_partner_ids', 'in', odoobot.id)])
                for c in ch:
                    if len(c.channel_last_seen_partner_ids) == 2:
                        ch = c
                        break
                # users = []
                # users.append(opp.user_id.id)
                # users.append(self.env.user.id)
                if not ch:
                    ch = ch_obj.sudo().create({
                        'name': 'Home Bot',
                        'public': 'private',
                        'channel_last_seen_partner_ids': [
                            (0, None, {
                                'partner_id': odoobot.id,
                            }),
                            (0, None, {
                                'partner_id': partner.id,
                            }),
                        ]
                    })
                ch.sudo().message_post(attachment_ids=[],
                                       body="Meeting "+rec.name+" has been cancelled",
                                       content_subtype='html',
                                       message_type='comment', partner_ids=[], subtype='mail.mt_comment',
                                       email_from=odoobot.email, author_id=odoobot.id)

        return super(CalendarMailActivity, self).unlink()

    def compute_join_attendee(self):
        event = self.env['calendar.attendee'].sudo().search([('event_id', '=', self.id)])
        user = self.env['res.users'].sudo().search([('id', '=', request.session.uid)])
        state = ['accepted', 'declined']
        for e in event:
            if e.partner_id.id == user.partner_id.id:
                e.do_accept()
                if e.state in state:
                    self.env['mail.activity'].sudo().search(
                        [('res_id', '=', self.id), ('user_id', '=', self.env.uid)]).action_done()

    def compute_decline_attendee(self):
        event = self.env['calendar.attendee'].sudo().search([('event_id', '=', self.id)])
        user = self.env['res.users'].sudo().search([('id', '=', request.session.uid)])
        state = ['accepted', 'declined']
        for e in event:
            if e.partner_id.id == user.partner_id.id:
                e.do_decline()
                if e.state in state:
                    self.env['mail.activity'].sudo().search(
                        [('res_id', '=', self.id), ('user_id', '=', self.env.uid)]).action_done()

    def mark_done_overdue_activity(self):
        today = date.today() - timedelta(days=3)
        meeting = self.env.ref('advanced_conference_room.mail_act_meeting').id
        self.env['mail.activity'].sudo().search([('date_deadline', '<', today),
                                                 ('res_model', '=', 'calendar.event'),
                                                 ('activity_type_id', '=', meeting)]).action_done()
