(function() {
    "use strict"; // http://bit.ly/4WwUAQ

    var SearchModel = Backbone.Model.extend({
            defaults: { "name": null }
        });

    var SearchCollection = Backbone.Collection.extend({
        model: SearchModel,
        url: "get_json"
    });

    // renders one <option> element based on "SearchModel"
    var SelectView = Backbone.View.extend({
        tagName: "option",

        initialize: function () { this.render(); },

        render: function () {
            var name = this.model.get("name");
            $(this.el).attr({"value": name, "class": "appended"}).html(name);
        }
    });

    /*
        Handles events for a select filter and.
        - checks to see if select has data or not, if the select has no data,
        the "SearchCollection" is fetched.
        - render all the <option> elements from "SearchCollection"
    */
    var SearchView = Backbone.View.extend({
        events: { "click": "fetch" },

        initialize: function () {
            this.collection = new SearchCollection();
            // when the collection is fetched, populate element with data
            this.collection.on("reset", this.populate, this);

            this.searched_field = this.el.id.replace("_chzn", "");
            // el is the "choosen" dropbox, parent is the select element
            this.$select_parent = $(_.sprintf("#%s", this.searched_field));
            // source data may depend on parent value
            this.parentData = this.options.parentData;

            var hooks = this.options.hooks || {};
            // callback that runs when the users select an option
            hooks.hookSelect = hooks.hookSelect || new Function();
            _.extend(this, hooks);

            // bind the change event for select parent to hookSelect
            this.$select_parent.unbind("change").bind("change", this.hookSelect);
        },

        // fetch collection if no data
        fetch: function () {
            // do not fetch collection if select element has data
            if(this.$select_parent.data("has-data")) { return; }
            var params = this._setFetchParams();
            this.collection.fetch({ data: params });
        },

        // populate the select element with data from "SearchCollection"
        populate: function () {
            var self = this;
            this.collection.each(function(m) {
                var select_view = new SelectView({ model: m });
                self.$select_parent.append(select_view.el);
            });
            // remember that select has data and refresh choosen plugin to update data
            self.$select_parent.data("has-data", true).trigger("liszt:updated");
        },

        _setFetchParams: function () {
            var params = {};
            params.searched_field = this.searched_field;
            if(this.parentData) {
                var query = $(_.sprintf("#%s", this.parentData)).val();
                if(query) {
                    params.query_field = this.parentData;
                    params.query = query;
                }
            }
            return params;
        },
    });

    // handle reset filters
    var _resetSelectFields = function () {
       // convert arguments object to array.
       var $selector = _constructSelectorFromArguments(arguments);
       $selector.find(".appended").remove();
       $selector.data("has-data", false).trigger("liszt:updated");
    };
    var _resetSelectChznFields = function () {
        var $selector = _constructSelectorFromArguments(arguments);
        $selector.find(".search-choice-close").remove();
    };
    var _constructSelectorFromArguments = function(args) {
        args = Array.prototype.slice.call(args, 0);
        return $(_.join(", ", args));
    };

    $(function() {
        /* Add flavor and autocomplete to select folders.
           http://harvesthq.github.com/chosen/ */
        $(".chzn-select").each(function() {
            // Jquery can't read data-placeholder with data method.
            // I think it's a version problem.
            $(this).data("placeholder", $(this).attr("data-placeholder"));
        }).chosen({
             allow_single_deselect: true
         });

         $(".search-form").bind("reset", function() {
             $(this).find(".chzn-select").val("").trigger("liszt:updated");
             $(".search-choice-close").remove();
         });

        new SearchView({ el: "#InstitutionCode_chzn" });
        new SearchView({ el: "#CollectionCode_chzn" });
        new SearchView({ el: "#BasisOfRecord_chzn" });
        new SearchView({ el: "#Country_chzn" });
        new SearchView({ el: "#Locality_chzn" });

        new SearchView({
            el: "#Family_chzn",
            hooks: {
                hookSelect: function () {
                    _resetSelectFields("#Genus", "#Species");
                    _resetSelectChznFields("#Genus_chzn", "#Species_chzn");
                }
            }
        });
        new SearchView({
            el: "#Genus_chzn",
            hooks: {
                hookSelect: function () {
                     _resetSelectFields("#Species");
                     _resetSelectChznFields("#Species_chzn");
                }
            },
            parentData: "Family"
        });
        new SearchView({
            el: "#Species_chzn",
            parentData: "Genus"
        });
    });
}());