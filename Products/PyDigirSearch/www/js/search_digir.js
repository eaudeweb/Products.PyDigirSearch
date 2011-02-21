$(document).ready(function(){
    var family_el = $('#Family');
    var genus_el = $('#Genus');
    var species_el = $('#Species');
    
    $.widget( "ui.combobox", { 
			_create: function() {
				var self = this,
					select = this.element.hide(),
					selected = select.children( ":selected" ),
					value = selected.val() ? selected.text() : "";
				var input = this.input = $("<input>")
					.insertAfter( select )
					.val( value )
					.autocomplete({
						delay: 0,
						minLength: 0,
						source: function( request, response ) {
						    if (select.attr('id') == 'Family'){
						        $.getJSON("get_json", {'type': 'families', 'value': request.term}, function(data){
    						        response(data.map(function(item) {
        						        return {
        						            label: item.Family,
        					                value: item.Family,
        					                option: this,
        						        }
        						    }));
    						    });
						    }else{
						        var matcher = new RegExp( $.ui.autocomplete.escapeRegex(request.term), "i" );
        						response( select.children( "option" ).map(function() {
        							var text = $( this ).text();
        							if ( this.value && ( !request.term || matcher.test(text) ) )
        								return {
        									label: text.replace(
        										new RegExp(
        											"(?![^&;]+;)(?!<[^<>]*)(" +
        											$.ui.autocomplete.escapeRegex(request.term) +
        											")(?![^<>]*>)(?![^&;]+;)", "gi"
        										), "<strong>$1</strong>" ),
        									value: text,
        									option: this
        								};
        						}) );
        					}
						},
						select: function( event, ui ) {
							ui.item.option.selected = true;
							self._trigger( "selected", event, {
								item: ui.item.option
							});
							
							if (select.attr('id') == 'Family'){
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
						    if (select.attr('id') == 'Genus'){
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
						},
						change: function( event, ui ) {
							if ( !ui.item ) {
								var matcher = new RegExp( "^" + $.ui.autocomplete.escapeRegex( $(this).val() ) + "$", "i" ),
									valid = false;
								select.children( "option" ).each(function() {
									if ( $( this ).text().match( matcher ) ) {
										this.selected = valid = true;
										return false;
									}
								});
								if ( !valid ) {
									// remove invalid value, as it didn't match anything
									$( this ).val( "" );
									select.val( "" );
									input.data( "autocomplete" ).term = "";
									return false;
								}
							}
						}
					})
					.addClass( "ui-widget ui-widget-content ui-corner-left" );

				input.data( "autocomplete" )._renderItem = function( ul, item ) {
					return $( "<li></li>" )
						.data( "item.autocomplete", item )
						.append( "<a>" + item.label + "</a>" )
						.appendTo( ul );
				};

				this.button = $( "<button type='button'>&nbsp;</button>" )
					.attr( "tabIndex", -1 )
					.attr( "title", "Show All Items" )
					.insertAfter( input )
					.button({
						icons: {
							primary: "ui-icon-triangle-1-s"
						},
						text: false
					})
					.removeClass( "ui-corner-all" )
					.addClass( "ui-corner-right ui-button-icon" )
					.click(function() {
						// close if already visible
						if ( input.autocomplete( "widget" ).is( ":visible" ) ) {
							input.autocomplete( "close" );
							return;
						}

						// pass empty string as value to search for, displaying all results
						input.autocomplete( "search", "" );
						input.focus();
					});
			},

			destroy: function() {
				this.input.remove();
				this.button.remove();
				this.element.show();
				$.Widget.prototype.destroy.call( this );
			}
		});
    
    family_el.combobox();
    genus_el.combobox();
    species_el.combobox();
})
