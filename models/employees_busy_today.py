from odoo import models, fields, api


class EmployeesBusyToday(models.Model):
    _name = 'employees.busy.today'

    @api.model
    def show_employees_busy_today(self, record=None):
        # show employees busy now
        # today = fields.Datetime.now()
        # self.env.cr.execute(''' SELECT partner_id FROM calendar_attendee WHERE event_id IN (
        #                         SELECT id FROM calendar_event WHERE (%s BETWEEN start AND stop))
        #                                 ''', (today,))
        # show employee busy today
        today = fields.Date.today()
        self.env.cr.execute(''' SELECT partner_id FROM calendar_attendee WHERE event_id IN (
                                SELECT id FROM calendar_event WHERE (%s BETWEEN date(start) AND date(stop)))
                                ''', (today,))
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
        # self.employees = hr_employee
        return hr_employee

    employees = fields.Many2many('hr.employee', default=show_employees_busy_today)
