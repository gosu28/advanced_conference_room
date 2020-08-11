from datetime import timedelta

import pytz
from pytz import timezone
from datetime import date
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class CalendarInherit(models.Model):
    _inherit = 'calendar.event'
    tasks = fields.One2many('conference.template.line', 'conference_template_task', copy=True)
    location_room = fields.Many2one('conference.room', string='Location', copy=False)
    conference_template = fields.Many2one('conference.template', 'Description Template')
    res_model_string = fields.Char('Document', compute='_compute_res_model_string')
    location_rooms = fields.Many2many('conference.room', string='Locations', copy=False)
    create_by_duplicate = fields.Boolean(
        string='Create by duplicate',
        required=False, )

    @api.onchange('duration', 'name')
    def _check_duration(self):
        for rec in self:
            if rec.name and rec.duration <= 0:
                rec.duration = 0.5

    @api.onchange('location_rooms', 'start_datetime', 'stop_datetime')
    def _onchange_location_rooms(self):
        if str(self.start_datetime) and str(self.start_datetime) < str(fields.Datetime.now()):
            self.start_datetime = fields.Datetime.now()
            return {
                'warning': {
                    'title': "Warning",
                    'message': "You Can Not Create A Meeting In The Past",
                }
            }
        if self.location_rooms and self.start_datetime and self.stop_datetime:
            start = (self.start_datetime + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
            end = (self.stop_datetime - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
            if self._origin.id:
                self.env.cr.execute('''SELECT conference_room_id FROM calendar_event_conference_room_rel WHERE calendar_event_id IN (
                                       SELECT id FROM calendar_event
                                       WHERE ((%s BETWEEN start AND stop) OR (%s BETWEEN start AND stop) OR ((start BETWEEN %s AND %s) AND (stop BETWEEN %s AND %s) )) and active=TRUE  AND (id not in %s))''',
                                    (start, end, start, end, start, end, (self._origin.id,)))
            else:
                self.env.cr.execute('''SELECT conference_room_id FROM calendar_event_conference_room_rel WHERE calendar_event_id in (
                                       SELECT id FROM calendar_event
                                       WHERE ((%s BETWEEN start AND stop) OR (%s BETWEEN start AND stop) OR ((start BETWEEN %s AND %s) AND (stop BETWEEN %s AND %s)))  and active=TRUE )''',
                                    (start, end, start, end, start, end))
            location_rooms_list = self.env.cr.fetchall()
            location_rooms_id_list = []
            for a in self.location_rooms:
                location_rooms_id_list.append(a.id.origin)
            for a in location_rooms_list:
                if a[0] in location_rooms_id_list:
                    raise UserError(_("This Room Not Available This Time"))

    def _compute_res_model_string(self):
        for rec in self:
            rec.res_model_string = ''
            if rec.res_model:
                rec.res_model_string = self.env['ir.model'].sudo()._get(self.res_model).display_name + " (1)"

    @api.onchange('conference_template')
    def onchange_conference_template(self):
        if self.conference_template:
            for line in self.conference_template:
                line_ids = line.conference_template_line_id
                self.tasks = line_ids

    def get_timezone(self):
        # get timezone
        user_time_zone = pytz.UTC
        if self.env.user.partner_id.tz:
            # change the timezone to the timezone of the user
            user_time_zone = pytz.timezone(self.env.user.partner_id.tz)
        return user_time_zone.zone

    @api.onchange('partner_ids', 'start_datetime', 'duration', 'location_rooms')
    def _onchange_partner_id(self):
        if self.partner_ids and self.start and self.stop:
            start = (self.start + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
            stop = (self.stop - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
            if len(self.partner_ids) > 0:
                for e in self.partner_ids:
                    current_partner = e.ids[0]
                    if self._origin and self._origin.id:
                        self.env.cr.execute('''
                                                            SELECT partner_id, event_id FROM calendar_attendee WHERE event_id IN (
                                                            SELECT id FROM calendar_event WHERE ((%s BETWEEN start AND stop) 
                                                                                                 OR (%s BETWEEN start AND stop)) and active=TRUE )
                                                            AND partner_id = %s AND state='accepted' AND event_id != %s
                                                           ''', (start, stop, current_partner, self._origin.id))
                    else:
                        self.env.cr.execute('''
                                                                                        SELECT partner_id, event_id FROM calendar_attendee WHERE event_id IN (
                                                                                        SELECT id FROM calendar_event WHERE ((%s BETWEEN start AND stop) 
                                                                                                                             OR (%s BETWEEN start AND stop)) and active=TRUE )
                                                                                        AND partner_id = %s AND state='accepted'
                                                                                       ''',
                                            (start, stop, current_partner,))
                    all_current_partner_event = self.env.cr.fetchall()
                    if all_current_partner_event and len(all_current_partner_event) > 0:
                        current_event = self.env['calendar.event'].sudo().browse(all_current_partner_event[0][1])
                        busy_from = current_event.start.astimezone(timezone(self.get_timezone())).strftime(
                            '%Y-%m-%d %H:%M:%S')
                        busy_to = current_event.stop.astimezone(timezone(self.get_timezone())).strftime(
                            '%Y-%m-%d %H:%M:%S')
                        raise UserError(_(e.name + " is busy From "
                                          + str(busy_from) + " To " + str(busy_to)))

    def unlink(self):
        for rec in self:
            if rec._uid != rec.create_uid.id and not self.env.user.has_group('base.group_system'):
                raise ValidationError(_('Can Not Delete This Record.Please Contact With Your Admin'))
        super(CalendarInherit, self).unlink()
        for rec in self:
            self.env['booked.calendar.event'].sudo().search([('booked_calendar_event_id', '=', rec.id)]).unlink()

    @api.model
    def create(self, vals):
        if vals.get('create_by_duplicate') == False:
            force_create = False
            if 'force_create_by_leave' in self._context:
                force_create = self._context['force_create_by_leave']
            if str(vals.get('start_datetime')) and str(vals.get('start_datetime')) < str(fields.Datetime.now()) and not force_create:
                raise UserError(_("You Can Not Create A Meeting In The Past"))
            if vals.get('location_rooms'):
                if not vals.get('tasks'):
                    raise ValidationError(_('Can Not Create Meeting without Tasks (Host, Plan, ...) at the bottom'))
            return super(CalendarInherit, self).create(vals)
        else:
            self = self.with_context(
                create_by_duplicate=vals['create_by_duplicate'],
            )
            return super(CalendarInherit, self).create(vals)

    def write(self, vals):
        if str(vals.get('start_datetime')) and str(vals.get('start_datetime')) < str(fields.Datetime.now()):
            raise UserError(_("You Can Not Create A Meeting In The Past"))
        old_rooms = self.location_rooms
        for rec in self:
            if len(rec.partner_ids) == 0:
                raise UserError(_("Meeting Should Has At Least 1 Member!"))
        result = super(CalendarInherit, self).write(vals)
        if 'location_rooms' in vals or 'start_datetime' in vals or 'duration' in vals:
            if len(old_rooms) > 0:
                for rec in self:
                    self.env['booked.calendar.event'].sudo().search([('booked_calendar_event_id', '=', rec.id)]).unlink()
            for rec in self:
                for a in rec.location_rooms:
                    self.env['booked.calendar.event'].sudo().create({
                        'booked_calendar_event_id': rec.id,
                        'name': a.name,
                        'start': rec.start,
                        'stop': rec.stop,
                        'location_room': a.id
                    })
        if vals.get('location_rooms'):
            for rec in self:
                if rec.create_by_duplicate == True:
                    rec.create_by_duplicate = False
                    partner_ids = []
                    state = ['accepted', 'declined']
                    attendee_ids = rec.env['calendar.attendee'].sudo().search([('event_id', '=', rec.id)])
                    for attendee_id in attendee_ids:
                        if attendee_id.state not in state:
                            partner_ids.append(attendee_id.partner_id.id)
                    user_ids = rec.env['res.users'].sudo().search([('partner_id', '=', partner_ids)])
                    for user_id in user_ids:
                        rec.activity_schedule('advanced_conference_room.mail_act_meeting', date_deadline=date.today(),
                                              user_id=user_id.id, automated=True, calendar_event_id=rec.id)

        for rec in self:
            if rec.location_rooms and len(rec.location_rooms) > 0:
                if rec.tasks and len(rec.tasks) > 0:
                    a = 0
                else:
                    raise ValidationError(_('Can Not Create Meeting without Tasks (Host, Plan, ...) at the bottom'))
        return result

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        copy = super(CalendarInherit, self).copy(default={'create_by_duplicate': True})
        return copy
    def create_attendees(self):
        current_user = self.env.user
        result = {}
        for meeting in self:
            alreay_meeting_partners = meeting.attendee_ids.mapped('partner_id')
            meeting_attendees = self.env['calendar.attendee']
            meeting_partners = self.env['res.partner']
            for partner in meeting.partner_ids.filtered(lambda partner: partner not in alreay_meeting_partners):
                values = {
                    'partner_id': partner.id,
                    'email': partner.email,
                    'event_id': meeting.id,
                }

                if self._context.get('google_internal_event_id', False):
                    values['google_internal_event_id'] = self._context.get('google_internal_event_id')

                # current user don't have to accept his own meeting
                if partner == self.env.user.partner_id:
                    values['state'] = 'accepted'

                attendee = self.env['calendar.attendee'].create(values)

                meeting_attendees |= attendee
                meeting_partners |= partner

            if meeting_attendees and not self._context.get('detaching') and not self._context.get('create_by_duplicate'):
                to_notify = meeting_attendees.filtered(lambda a: a.email != current_user.email)
                to_notify._send_mail_to_attendees('calendar.calendar_template_meeting_invitation')

            if meeting_attendees:
                meeting.write({'attendee_ids': [(4, meeting_attendee.id) for meeting_attendee in meeting_attendees]})

            if meeting_partners:
                meeting.message_subscribe(partner_ids=meeting_partners.ids)

            # We remove old attendees who are not in partner_ids now.
            all_partners = meeting.partner_ids
            all_partner_attendees = meeting.attendee_ids.mapped('partner_id')
            old_attendees = meeting.attendee_ids
            partners_to_remove = all_partner_attendees + meeting_partners - all_partners

            attendees_to_remove = self.env["calendar.attendee"]
            if partners_to_remove:
                attendees_to_remove = self.env["calendar.attendee"].search([('partner_id', 'in', partners_to_remove.ids), ('event_id', '=', meeting.id)])
                attendees_to_remove.unlink()

            result[meeting.id] = {
                'new_attendees': meeting_attendees,
                'old_attendees': old_attendees,
                'removed_attendees': attendees_to_remove,
                'removed_partners': partners_to_remove
            }
        return result

class CalendarEventPartner(models.Model):
    _inherit = 'calendar.event'

    def write(self, vals):
        # self.ensure_one()
        if vals.get('partner_ids'):
            for rec in self:
                # find old partner_ids
                old_partner_ids = [e.partner_id.id for e in self.env['mail.followers'].sudo().search(
                    [('res_id', '=', rec.id), ('res_model', '=', 'calendar.event')])]
                result = super(CalendarEventPartner, self).write(vals)
                new_partner_ids = [e.id for e in self.env['calendar.event'].browse(rec.id).partner_ids]
                for e in old_partner_ids:
                    if e not in new_partner_ids:
                        self.env['mail.followers'].sudo().search(
                            [('res_id', '=', rec.id), ('res_model', '=', 'calendar.event'),
                             ('partner_id', '=', e)]).unlink()
                return result
        else:
            return super(CalendarEventPartner, self).write(vals)
