from odoo import fields, models


class UpdateBookedCalendarEvent(models.Model):
    _name = 'update.booked.calendar.event'
    response = fields.Char(readonly=1)

    def compute_update_booked_calendar_event(self):
        self.env.cr.execute('''SELECT meeting_id FROM hr_leave WHERE id > 0''')
        all_meeting_ids_db = self.env.cr.fetchall()
        all_meeting_ids = []
        for e in all_meeting_ids_db:
            if e[0]:
                all_meeting_ids.append(str(e[0]))
        locations_events_list1 = self.env['booked.calendar.event'].sudo()

        # update location_rooms select multiple locations instead of a location(create)
        self.env.cr.execute("""SELECT calendar_event_id, conference_room_id FROM calendar_event_conference_room_rel 
                                WHERE calendar_event_id IN (SELECT id FROM calendar_event
                                    WHERE active=TRUE and id NOT IN (SELECT booked_calendar_event_id FROM  booked_calendar_event)
                                            AND id NOT IN (%s))
                                """ % ','.join(all_meeting_ids))
        location_room_id_list1 = self.env.cr.fetchall()
        self.env.cr.execute("""
                        SELECT id, start, stop FROM calendar_event
                        WHERE active=TRUE and id NOT IN (SELECT booked_calendar_event_id FROM  booked_calendar_event)
                            AND id IN (SELECT calendar_event_id FROM calendar_event_conference_room_rel)
                            AND id NOT IN (%s)
                        """ % ','.join(all_meeting_ids))
        id_start_stop_list1 = self.env.cr.fetchall()

        if location_room_id_list1 and id_start_stop_list1:
            events_need_insert_lists1 = []
            for i in location_room_id_list1:
                for j in id_start_stop_list1:
                    if j[0] == i[0]:
                        lists1 = [i[0], j[1], j[2], i[1]]
                        events_need_insert_lists1.append({
                            'booked_calendar_event_id': lists1[0],
                            'name': 'Occupied',
                            'start': lists1[1],
                            'stop': lists1[2],
                            'location_room': lists1[3]
                        })
            locations_events_list1.create(events_need_insert_lists1)

        # update location_rooms select multiple locations instead of a location(update)
        locations_events_list2 = self.env['booked.calendar.event'].sudo()
        self.env.cr.execute("""SELECT calendar_event_id, conference_room_id FROM calendar_event_conference_room_rel WHERE calendar_event_id
                                        IN (SELECT id FROM calendar_event
                                            WHERE active=TRUE and id IN (SELECT booked_calendar_event_id FROM  booked_calendar_event)
                                                    AND id NOT IN (%s))
                                        """ % ','.join(all_meeting_ids))
        location_room_id_list2 = self.env.cr.fetchall()
        self.env.cr.execute("""
                                SELECT id, start, stop FROM calendar_event
                                WHERE active=TRUE and id NOT IN (SELECT booked_calendar_event_id FROM  booked_calendar_event)
                                    AND id IN (SELECT calendar_event_id FROM calendar_event_conference_room_rel)
                                    AND id NOT IN (%s)
                                """ % ','.join(all_meeting_ids))
        id_start_stop_list2 = self.env.cr.fetchall()

        if location_room_id_list2 and id_start_stop_list2:
            for i in location_room_id_list1:
                for j in id_start_stop_list1:
                    if j[0] == i[0]:
                        lists2 = [i[0], j[1], j[2], i[1]]
                        locations_events_list2.search([('booked_calendar_event_id', '=', i[0])]).update({
                            'booked_calendar_event_id': lists2[0],
                            'name': 'Occupied',
                            'start': lists2[1],
                            'stop': lists2[2],
                            'location_room': lists2[3]
                        })
            # locations_events_list2.update(events_need_insert_lists2)

        # update select only a location_room(create)
        events_list1 = self.env['booked.calendar.event'].sudo()
        self.env.cr.execute("""
                        SELECT id, start, stop, location_room FROM calendar_event
                        WHERE active=TRUE and id NOT IN (SELECT booked_calendar_event_id FROM  booked_calendar_event)
                        AND location_room > 0
                        AND id NOT IN (%s)
                        """ % ','.join(all_meeting_ids))
        event_list1 = self.env.cr.fetchall()
        if event_list1:
            events_need_insert1 = []
            for a in event_list1:
                events_need_insert1.append({
                    'booked_calendar_event_id': a[0],
                    'name': 'Occupied',
                    'start': a[1],
                    'stop': a[2],
                    'location_room': a[3]
                })
            events_list1.create(events_need_insert1)

        # update select only a location_room(update)
        self.env.cr.execute(""" SELECT id, start, stop, location_room FROM calendar_event
                                WHERE active=TRUE and id IN (SELECT booked_calendar_event_id FROM  booked_calendar_event)
                                AND location_room > 0
                                AND id NOT IN (%s)
                                 """ % ','.join(all_meeting_ids))
        event_list2 = self.env.cr.fetchall()
        events_list2 = self.env['booked.calendar.event'].sudo()
        if event_list2:
            # events_need_insert2 = []
            for a in event_list2:
                events_list2.search([('booked_calendar_event_id', '=', a[0])]).update({
                    'name': 'Occupied',
                    'start': a[1],
                    'stop': a[2],
                    'location_room': a[3]
                })
            # events_list2.update(events_need_insert2)
        self.response = str(len(event_list1) + len(id_start_stop_list1)) + " records created" + "\n" + str(
            len(event_list2) + len(id_start_stop_list1)) + " records updated"
