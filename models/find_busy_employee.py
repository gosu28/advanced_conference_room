from odoo import fields, models, api


class findBusyEmployee(models.Model):
    _name = 'find.busy.employee'
    date_from = fields.Datetime('Date from')
    date_to = fields.Datetime('Date to')
    employees = fields.Many2many('hr.employee')

    @api.onchange('date_from', 'date_to')
    def _onchange_busy_employee(self):
        if self.date_from and self.date_to:
            # tim cac busy employee from start to end
            start = self.date_from.strftime('%Y-%m-%d %H:%M:%S')
            end = self.date_to.strftime('%Y-%m-%d %H:%M:%S')
            self.env.cr.execute('''
                                    SELECT partner_id FROM calendar_attendee WHERE event_id IN (
                                        SELECT id FROM calendar_event WHERE (%s BETWEEN start AND stop) 
                                                                            OR (%s BETWEEN start AND stop))
                                    ''', (start, end))
            employee_busy = self.env.cr.fetchall()

            list_employee_busy = []
            for a in employee_busy:
                list_employee_busy.append(a[0])
            users_employee_busy = self.env['res.users'].sudo().search([('partner_id', 'in', list_employee_busy)])

            employee_busy_id = []
            for a in users_employee_busy:
                employee_busy_id.append(a.id)
            res_users2 = self.env['hr.employee'].search([('user_id', 'in', employee_busy_id)])

            list_employee_busy_id = []
            for a in res_users2:
                list_employee_busy_id.append(a.id)

            # tim cac employee la manager cua minh, hoac la nhan vien cua minh, hoac cung manager
            user_id = self.env.user.id
            emp = self.env['hr.employee'].search([('user_id', '=', user_id)])
            manager = emp[0].parent_id
            subordinates = emp[0].child_ids

            subordinates_child_list = []
            for a in subordinates:
                subordinates_child_list.append(a.id)
            subordinates_child = self.env['hr.employee'].search([('id', 'in', subordinates_child_list)])
            subordinates_child_child_list = []
            for a in subordinates_child:
                subordinates_child_child_list.append(a[0].child_ids)

            employee = emp + manager + manager.child_ids + subordinates
            for e in subordinates_child_child_list:
                employee += e
            list_relate_user = []
            for a in employee:
                list_relate_user.append(a.id)

            # dua vao 2 list ben tren loc ra cac employee ban can hien thi
            hr_employee = []
            for user_busy in list_employee_busy_id:
                for relate_user in list_relate_user:
                    if user_busy == relate_user:
                        hr_employee.append(user_busy)

            # gan self.employees = result
            self.employees = hr_employee

            # lay tat ca cac ban ghi attendee dang ban dang ban trong ngay so sanh start hoac stop nam trong date_from den date_to
