$(document).ready(function(){

$.widget("ui.combobox", {
	options: {
		source: function(request, response){
			options_source(this, request, response);
		},
		select: function(event, ui) {
			ui.item.option.selected = true;
			//Set value to the select
			var select = $('#' + $(this).attr('target'));
			if(select.find("[value="+ ui.item.value +"]")){
				select.append($("<option>").val(ui.item.value));
			}
			select.val(ui.item.value).trigger("change");
		},
		change: function(event, ui) {
			var self = $(this);
			var select = $('#' + self.attr('target'));

			if (!ui.item) {
				var matcher = new RegExp("^" + $.ui.autocomplete.escapeRegex(self.val()) + "$", "i"),
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
				delay: 300,
				minLength: 2,
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
				input.autocomplete("option", 'minLength', [0]);
				// pass empty string as value to search for, displaying all results
				input.autocomplete("search", input.val());
				input.focus();
				//Revert to the previous length
				input.autocomplete("option", 'minLength', [2]);
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
var institution_el = $('#InstitutionCode');
var collection_el = $('#CollectionCode');
var basisofrecord_el = $('#BasisOfRecord');
var country_el = $('#Country');


function options_source(self, request, response){
	var select = $('#' + self.element.attr('target'));
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
}

function handle_source(type, request, response){
	$.getJSON("get_json", {'type': type, 'value': request.term}, function(data){
		response(data.map(function(item) {
			for (i in item){
				return {
					label: item[i],
					value: item[i],
					option: this
				}
			}
		}));
	});
}

institution_el.combobox({
	source: function(request, response){
		handle_source('institutions', request, response);
	}
});

collection_el.combobox({
	source: function(request, response){
		handle_source('collections', request, response);
	}
});

basisofrecord_el.combobox({
	source: function(request, response){
		handle_source('basisofrecords', request, response);
	}
});

family_el.combobox({
	source: function(request, response){
		handle_source('families', request, response);
	},
	select: function(event, ui){
		ui.item.option.selected = true;

		//Set value to the select
		var select = $('#' + $(this).attr('target'));
		if(select.find("[value="+ ui.item.value+"]")){
			select.append($("<option>").val(ui.item.value));
		}
		select.val(ui.item.value).trigger("change");

		genus_el.empty();
		species_el.empty();

		$.getJSON('get_json', {'type': 'genus_by_family',
				  'value': ui.item.value}, function(data){
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
	source: function(request, response){
		if (genus_el.children("option").length > 0){
			options_source(this, request, response);
		}else{
			handle_source('genus', request, response);
		}
	},
	select: function(event, ui){
		ui.item.option.selected = true;
		species_el.empty();
		$.getJSON('get_json', {'type': 'species_by_genus', 'value': ui.item.value},
				  function(data){
			$.each(data, function(){
				var val = this.Species;
				var new_option = $("<option>").val(val).text(val);
				species_el.append(new_option);
			});
		});
		return;
	}
});

species_el.combobox({
	source: function(request, response){
		if (species_el.children("option").length > 0){
			options_source(this, request, response);
		}else{
			handle_source('species', request, response);
		}
	},
});

names_el.combobox({
	source: function(request, response){
		handle_source('names', request, response);
	},
});

country_el.combobox({
	source: function(request, response){
		handle_source('countries', request, response);
	},
});

locality_el.combobox({
	source: function(request, response){
		handle_source('localities', request, response);
	},
});


$("#reset-button").click(function(){
	$("select").empty();
});
});
