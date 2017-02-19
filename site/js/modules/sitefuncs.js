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

export function parseAppCallbackUrl( url ) {
	var neededAssurances,
		appDomain
	if ( url ) {
		var a = decodeURIComponent( url ).split("?"),
			vars = QueryStringFunc('?'+a[1]);
		if (vars.redirect_uri) {
			var c = decodeURIComponent(vars.redirect_uri).split("?")
			appDomain=c[0].split('://')[1].split('/')[0]
			var b = QueryStringFunc('?'+c[1])
			if (b.need)	neededAssurances = b.need.split(',')
		}
	}
	return { appdomain: appDomain, neededAssurances: neededAssurances }
}