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
			};
		}
	}));
}

function handle_source(searched_field, query_field, request, response) {
	params = {  'query': request.term, 'searched_field': searched_field };
	if (query_field) params.query_field = query_field;

	$.getJSON("get_json", params,
	function(data) {
		var values = [];
		$.each(data, function(i, item) {
			values.push({
				label:item,
				value: item,
				option: this
			});
		});
		response(values);
	});
}
/**
 * Set select target with the current value.
*/
function set_select(obj, ui){
	//Set value to the select
	var select = $('#' + obj.attr('target'));
	// Don't add this option if it's already in select
	if(select.find("[value="+ ui.item.value +"]").size() === 0){
		select.append($("<option>").val(ui.item.value));
	}
	select.val(ui.item.value).trigger("change");
}

$(document).ready(function(){
/**
 * A new Jquery ui widget using jquery autocomplete.
*/
$.widget("ui.combobox", {
	options: {
		source: function(request, response){
			options_source(this, request, response);
		},
		select: function(event, ui) {
			ui.item.option.selected = true;
			set_select($(this), ui);
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
					if (self.attr('target') === 'Family'){
						genus_el.empty();
					}
					if (self.attr('target') === 'Genus'){
						species_el.empty();
					}
					return false;
				}
			}
		}
	},

	_create: function() {
		var select = this.element.hide(),
			selected = select.children(":selected"),
			value = selected.val() ? selected.text() : "";

		var input = this.input = $("<input>")
			.insertAfter(select)
			.attr("target", select.attr('id'))
			.val(value)
			.autocomplete({
				delay: 300,
				minLength: 2,
				source: this.options.source,
				select: this.options.select,
				change: this.options.change
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

//Future comboboxes
var family_el = $('#Family');
var genus_el = $('#Genus');
var species_el = $('#Species');
var locality_el = $('#Locality');
var institution_el = $('#InstitutionCode');
var collection_el = $('#CollectionCode');
var basisofrecord_el = $('#BasisOfRecord');
var country_el = $('#Country');

//If the value of family is already set then get all genuses for that specific family
if(family_el.val()){
	$.getJSON('get_json', {searched_field: 'Genus',
							query: family_el.val(),
							query_field: 'Family'},
	function(data){
		$.each(data, function(){
			var val = this.toString();
			// Don't add this option if it's already in select
			if (genus_el.find("[value="+ val +"]").size() === 0){
				genus_el.append($("<option>").val(val).text(val));
			}
		});
	});
}

family_el.combobox({
	source: function(request, response){
		handle_source('Family', null, request, response);
	},
	select: function(event, ui){
		ui.item.option.selected = true;
		set_select($(this), ui);

		genus_el.empty();
		species_el.empty();

		$.getJSON('get_json', {searched_field: 'Genus',
							query: ui.item.value,
							query_field: 'Family'},
		function(data){
			$.each(data, function(){
				var val = this.toString();
				if (genus_el.find("[val="+ val +"]").size() === 0){
					genus_el.append($("<option>").val(val).text(val));
				}
			});
			//Add an empty option so that the request does not set the species automatically
			genus_el.append($("<option>").val("").text("All"));
			genus_el.val("");
		});
		return;
	}
});

//If the value of genus is already set then get all species for that specific genus
if(genus_el.val()){
	$.getJSON('get_json', {searched_field: 'Species',
							query: genus_el.val(),
							query_field: 'Genus'},
	function(data){
		$.each(data, function(){
			var val = this.toString();
			// Don't add this option if it's already in select
			if (species_el.find("[value="+ val +"]").size() === 0){
				species_el.append($("<option>").val(val).text(val));
			}
		});
	});
}

genus_el.combobox({
	source: function(request, response){
		if (genus_el.children("option").length > 0){
			options_source(this, request, response);
		}else{
			handle_source('Genus', null, request, response);
		}
	},
	select: function(event, ui){
		ui.item.option.selected = true;
		set_select($(this), ui);

		species_el.empty();
		$.getJSON('get_json', {searched_field: 'Species',
							query: ui.item.value,
							query_field: 'Genus'},
		function(data){
			$.each(data, function(){
				var val = this.toString();
				if (species_el.find("[value="+ val +"]").size() === 0){
					species_el.append($("<option>").val(val).text(val));
				}
			});
			//Add an empty option so that the request does not set the species automatically
			species_el.append($("<option>").val("").text("All"));
			species_el.val("");
		});
		return;
	}
});

species_el.combobox({
	source: function(request, response){
		if (species_el.children("option").length > 0){
			options_source(this, request, response);
		}else{
			handle_source('Species', null, request, response);
		}
	}
});

institution_el.combobox({
	source: function(request, response){
		handle_source('InstitutionCode', null, request, response);
	}
});

collection_el.combobox({
	source: function(request, response){
		handle_source('CollectionCode', null, request, response);
	}
});

basisofrecord_el.combobox({
	source: function(request, response){
		handle_source('BasisOfRecord', null, request, response);
	}
});

country_el.combobox({
	source: function(request, response){
		handle_source('Country', null, request, response);
	}
});

locality_el.combobox({
	source: function(request, response){
		handle_source('Locality', null, request, response);
	}
});


$("#reset-button").click(function(){
	$("select").empty();
});
});
