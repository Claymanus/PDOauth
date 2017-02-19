export function QueryStringFunc( search ) { //http://stackoverflow.com/questions/979975/how-to-get-the-value-from-the-url-parameter
	var query_string = {},
		query = search.substring( 1 ),
		vars = query.split( "&" )
	for ( var i=0; i<vars.length; i++ ) {
		var pair = vars[i].split( "=" )
		if ( typeof query_string[pair[0]] === "undefined" ) query_string[pair[0]] = pair[1] 
		else if (typeof query_string[pair[0]] === "string") {
			var arr = [ query_string[pair[0]], pair[1] ]
			query_string[pair[0]] = arr;
		} 
		else  query_string[pair[0]].push(pair[1])
	} 
    return query_string;
}