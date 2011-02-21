$(document).ready(function(){

$.widget("ui.combobox", {
	options: {
		source: function(request, response){
			var select = $('#' + this.element.attr('target'));
			var matcher = new RegExp($.ui.autocomplete.escapeRegex(request.term), "i");
			response(select.children("option").map(function() {
				var text = $(this).text();
				if (this.value && (!request.term || matcher.test(text))){
					return {
						label: text.replace(
							new RegExp(
								"(?![^&;]+;)(?!<[^<>]*)(" +
								$.ui.autocomplete.escapeRegex(request.term) +
								")(?![^<>]*>)(?![^&;]+;)", "gi"
							), "<strong>$1</strong>"),
						value: text,
						option: this
					}
				}
			}));
		},
		select: function(event, ui) {
			ui.item.option.selected = true;
		},
		change: function(event, ui) {
			var self = $(this);
			var select = $('#' + self.attr('target'));

			if (!ui.item) {
				var matcher = new RegExp("^" + $.ui.autocomplete.escapeRegex($(this).val()) + "$", "i"),
					valid = false;
				select.children("option").each(function() {
					if ($(this).text().match(matcher)) {
						this.selected = valid = true;
						return false;
					}
				});
				if (!valid) {
					// remove invalid value, as it didn't match anything
					$(this).val("");
					select.val("");
					return false;
				}
			}
		}
	},

	_create: function() {
		var self = this,
			select = this.element.hide(),
			selected = select.children(":selected"),
			value = selected.val() ? selected.text() : "";

		var input = this.input = $("<input>")
			.insertAfter(select)
			.attr("target", select.attr('id'))
			.val(value)
			.autocomplete({
				delay: 0,
				minLength: 0,
				source: this.options['source'],
				select: this.options['select'],
				change: this.options['change']
			}).addClass("ui-widget ui-widget-content ui-corner-left");

		input.data("autocomplete")._renderItem = function(ul, item) {
			return $("<li></li>")
				.data("item.autocomplete", item)
				.append("<a>" + item.label + "</a>")
				.appendTo(ul);
		};

		this.button = $("<button type='button'>&nbsp;</button>")
			.attr("tabIndex", -1)
			.attr("title", "Show All Items")
			.insertAfter(input)
			.button({
				icons: {
					primary: "ui-icon-triangle-1-s"
				},
				text: false
			})
			.removeClass("ui-corner-all")
			.addClass("ui-corner-right ui-button-icon")
			.click(function() {
				// close if already visible
				if (input.autocomplete("widget").is(":visible")) {
					input.autocomplete("close");
					return;
				}

				// pass empty string as value to search for, displaying all results
				input.autocomplete("search", "");
				input.focus();
			});
	},

	destroy: function() {
		this.input.remove();
		this.button.remove();
		this.element.show();
		$.Widget.prototype.destroy.call(this);
	}
});

var family_el = $('#Family');
var genus_el = $('#Genus');
var species_el = $('#Species');
var names_el = $('#ScientificNameAuthor');
var locality_el = $('#Locality');

family_el.combobox({
	source: function(request, response){
		$.getJSON("get_json", {'type': 'families', 'value': request.term}, function(data){
			response(data.map(function(item) {
				return {
					label: item.Family,
					value: item.Family,
					option: this
				}
			}));
		});
	},
	select: function(event, ui){
		ui.item.option.selected = true;
		genus_el.empty();
		species_el.empty();
		$.getJSON('get_json', {'type': 'genus', 'value': this.value}, function(data){
			$.each(data, function(){
				var val = this.Genus;
				var new_option = $("<option>").val(val).text(val);
				genus_el.append(new_option);
			});
		});
		return;
	}
});

genus_el.combobox({
	select: function(event, ui){
		ui.item.option.selected = true;
		species_el.empty();
		$.getJSON('get_json', {'type': 'species', 'value': this.value}, function(data){
			$.each(data, function(){
				var val = this.Species;
				var new_option = $("<option>").val(val).text(val);
				species_el.append(new_option);
			});
		});
		return;
	}
});

species_el.combobox();

names_el.combobox({
	source: function(request, response){
		$.getJSON("get_json", {'type': 'names', 'value': request.term}, function(data){
			response(data.map(function(item) {
				return {
					label: item.ScientificNameAuthor,
					value: item.ScientificNameAuthor,
					option: this
				}
			}));
		});
	},
});

locality_el.combobox({
	source: function(request, response){
		$.getJSON("get_json", {'type': 'localities', 'value': request.term}, function(data){
			response(data.map(function(item) {
				return {
					label: item.Locality,
					value: item.Locality,
					option: this
				}
			}));
		});
	},
});

});
