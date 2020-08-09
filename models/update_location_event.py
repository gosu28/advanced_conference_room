from odoo import fields, models


class UpdateLocationEvent(models.Model):
    _name = 'update.location.event'
    response = fields.Char(readonly=1)

    def compute_update_event(self):
        count_record_update = 0
        self.env.cr.execute('''SELECT id, location_room FROM calendar_event
                                    WHERE location_room > 0
                                    AND id NOT IN (SELECT calendar_event_id FROM calendar_event_conference_room_rel)''')
        event_location_list = self.env.cr.fetchall()

        if event_location_list:
            for a in event_location_list:
                self.env.cr.execute('''INSERT INTO calendar_event_conference_room_rel(calendar_event_id, conference_room_id)
                                            VALUES (%s, %s)''', (a[0], a[1]))
                count_record_update += 1
        if count_record_update > 0:
            self.response = str(count_record_update) + ' record update'
        else:
            self.response = 'Nothing update'
