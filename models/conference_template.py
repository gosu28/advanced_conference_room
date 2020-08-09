from odoo import models, fields


class ConferenceTemplate(models.Model):
    _name = 'conference.template'
    name = fields.Char('Description Template', required=True)
    conference_template_line_id = fields.One2many('conference.template.line', 'conference_template_id',
                                                  string="Description Lines")
    conference_template_select = fields.Many2one('calendar.event')


class ConferenceTemplateLine(models.Model):
    _name = 'conference.template.line'
    conference_template_id = fields.Many2one('conference.template')
    conference_template_task = fields.Many2one('calendar.event')
    # quotations_template_select = fields.Many2one('calendar.event')
    host = fields.Char('Host', required=True)
    task = fields.Char('Task')
    deadline = fields.Char('Deadline')
    plan = fields.Char('Plan')
