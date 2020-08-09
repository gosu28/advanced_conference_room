from odoo import models, fields, api


class ConferenceRoom(models.Model):
    _name = 'conference.room'
    name = fields.Char('Room', required=True)
    location = fields.Many2one('company.location', 'Location', required=True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if not self.user_has_groups('base.group_system') and not self.user_has_groups(
                'advanced_conference_room.conference_location_room_admin'):
            # find conference.room for each user
            company_location = 1
            current_user = self.env['res.users'].browse(self._uid)
            if len(current_user.employee_ids.ids) > 0:
                company_location = current_user.employee_ids[0].employee_location.id
            args = [('location', '=', company_location)] + list(args)
        return super(ConferenceRoom, self)._search(args, offset=offset, limit=limit, order=order, count=count,
                                                   access_rights_uid=access_rights_uid)
