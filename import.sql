.read fews_unblobbed_schema.sql
.separator \t
.import filter.dump filter
.import location.dump location
.import parameter.dump parameter
.import timeserie.dump timeserie
.import timeseriedata.dump timeseriedata
UPDATE filter SET parentfkey=NULL WHERE parentfkey='\N';
UPDATE location SET parentid=NULL WHERE parentid='\N';
UPDATE location SET tooltiptext=NULL WHERE tooltiptext='\N';
UPDATE timeseriedata SET tsd_comments=NULL WHERE tsd_comments='\N';
