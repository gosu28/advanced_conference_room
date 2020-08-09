from odoo import models, fields


class DisableDragDropCalendarEvent(models.Model):
    _inherit = 'calendar.event'
    start = fields.Datetime(
        'Date Start', readonly=True, index=True, copy=False, required=True,
        default=fields.Datetime.now,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, track_visibility='onchange')
    stop = fields.Datetime(
        'Date End', readonly=True, copy=False, required=True,
        default=fields.Datetime.now,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, track_visibility='onchange')
