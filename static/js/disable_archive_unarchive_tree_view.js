odoo.define("web_disable_archive_unarchive_button", function (require) {
    "use strict";

    var core = require("web.core");
    var Sidebar = require('web.Sidebar');
    var ListController = require("web.ListController");
    var _t = core._t;
    var session = require("web.session");

    ListController.include({

        /**
         * Render the sidebar (the 'action' menu in the control panel, right of the
         * main buttons)
         *
         * @param {jQuery Node} $node
         */
        renderSidebar: function ($node) {
            var model = this.modelName;
            var has_archive_group = false;
            if (this.hasSidebar && this.sidebar && model == 'calendar.event') {
                this.getSession().user_has_group('base.group_no_one').then(function (has_group) {
                    if (has_group) {
                        has_archive_group = true;
                    }
                });
            }
            this.archiveEnabled = true;
            if (!has_archive_group) {
                this.archiveEnabled = false
            }
            this._super.apply(this, arguments);
        }
    });
});
