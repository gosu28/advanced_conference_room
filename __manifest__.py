# -*- coding: utf-8 -*-
{
    'name': "Conference Room Management",
    'summary': """
        Magenest Conference Room Management""",
    'description': """
         Magenest Conference Room Management
    """,
    'author': "Magenest",
    'website': "https://store.magenest.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'calendar', 'hr', 'hr_holidays', 'company_location', 'account'],
    'data': [
        'security/security.xml',
        'data/mail_data.xml',
        'data/mark_done_overdue_activity_cron.xml',
        'data/calendar_templates.xml',
        'security/ir.model.access.csv',
        'views/employees_busy_menuitem_view.xml',
        'views/booked_calendar_event_view.xml',
        # 'views/calendar_by_location_view.xml',
        'views/calendar_event_inherit_views.xml',
        'views/conference_room.xml',
        'views/conference_template_view.xml',
        'views/employees_busy_today.xml',
        'views/find_busy_employee.xml',
        'views/update_event_view.xml',
        'views/xpath_filter_event_in_calendar.xml',
        'views/update_location_event_view.xml',
        'views/inherit_contacts_tree_view.xml',
        'views/related_employee.xml',
    ],
}
