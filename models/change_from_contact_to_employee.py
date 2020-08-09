from odoo import models
from odoo.http import request


class AdvancedRelatedEmployee(models.Model):
    _name = 'advanced.related.employee'

    # def _default_change_events(self):
    #     if self._context.get('active_ids'):
    #         return self.env['res.partner'].browse(self._context.get('active_ids'))
    #
    # change_contact = fields.Many2many('res.partner', string="Contact", required=True, default=_default_change_events)

    def compute_related_employee(self):
        # contacts_active = self.env['res.partner'].browse(e for e in self._context['active_ids'])
        # contacts_active_list = []
        # for a in contacts_active:
        #     contacts_active_list.append(a[0].id)
        # self.env.cr.execute('''SELECT * FROM res_partner WHERE is_employee != TRUE ''')
        # contact_list = self.env.cr.fetchall()
        # employee_list = self.env['hr.employee'].sudo()
        # for a in contact_list:
        #     if a[0] in contacts_active_list:
        #         employee_list.create({
        #             'name': a[1]
        #         })
        #
        #         change_status = self.env['res.partner'].sudo().search([('id', '=', a[0])])
        #         change_status.update({
        #             'is_employee': True
        #         })
        partners = self.env['res.partner'].sudo().search([])
        for e in partners:
            if e.user_ids and len(e.user_ids.filtered(lambda user: user.active == True).ids) > 0:
                e.write({
                    'employee': True
                })
        return {'type': 'ir.actions.act_window_close'}


class RemoveEmployee(models.Model):
    _inherit = 'hr.employee'

    def unlink(self):
        for rec in self:
            update_res = request.env['res.partner'].search(['|', ('name', '=', rec.name), ('employee', '=', True)])
            if update_res:
                update_res.update({
                    'employee': False
                })
        return super(RemoveEmployee, self).unlink()
