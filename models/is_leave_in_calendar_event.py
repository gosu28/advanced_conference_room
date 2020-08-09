from odoo import models, api, fields


class CalendarEventInherit(models.Model):
    _inherit = 'calendar.event'
    is_leave = fields.Boolean(string='Is Leave')

    @api.model
    def create(self, values):
        record = super(CalendarEventInherit, self).create(values)
        return record
