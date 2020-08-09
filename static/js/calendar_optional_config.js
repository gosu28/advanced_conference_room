odoo.define('calendar.disable.allday', function (require) {
    "use strict";
    var Calendar = require('web.CalendarModel');
    var core = require('web.core');
    var _t = core._t;
    Calendar.include({
        _getFullCalendarOptions: function () {
            // console.log(this.check_selectable());
            return {
                defaultView: (this.mode === "month") ? "month" : ((this.mode === "week") ? "agendaWeek" : ((this.mode === "day") ? "agendaDay" : "agendaWeek")),
                header: false,
                selectable: this.creatable && this.create_right,
                selectHelper: true,
                editable: this.editable,
                droppable: true,
                navLinks: false,
                eventLimit: this.eventLimit, // allow "more" link when too many events
                snapMinutes: 15,
                longPressDelay: 500,
                eventResizableFromStart: true,
                weekNumbers: true,
                weekNumberTitle: _t("W"),
                allDayText: _t("All day"),
                monthNames: moment.months(),
                allDaySlot: false,
                monthNamesShort: moment.monthsShort(),
                dayNames: moment.weekdays(),
                dayNamesShort: moment.weekdaysShort(),
                firstDay: _t.database.parameters.week_start,
                slotLabelFormat: _t.database.parameters.time_format.search("%H") != -1 ? 'H:mm' : 'h(:mm)a',
            };

        },
    });
});
