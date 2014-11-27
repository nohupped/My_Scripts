#!/usr/bin/perl
use strict;
use warnings;
use MongoDB;
use Data::Dumper;
use Sys::Hostname;


my $host=`hostname -f`;
chomp $host;
my $admindb="admin";
#my $pass="Password here";
my $collections;

##Connect
my $client = MongoDB::MongoClient->new(host => 'localhost', port => 27017);
my $dbadmin = $client->get_database( 'admin' ); 
$MongoDB::Cursor::slave_okay = 1; 

##Authenticate
##Uncomment the line below if auth is set.
#$client->authenticate("$admindb", 'mongoroot', "$pass");
$client->authenticate("$admindb","","");
##Find db names
my @dbs = $client->database_names;
#print @dbs;

##Find rs.status
#my $result = $dbadmin->run_command({serverStatus => 1});
#print "current : $result->{connections}->{current}\n";

###printing in yaml
print_yaml($host, \@dbs);

sub print_yaml{

	my ($hostname, $dbs) = @_;
my $numdbs = scalar @$dbs;
#print "  $hostname:\n";

foreach my $db (@$dbs){
        my $database = $client->get_database("$db");
       	my $dbstats = $database->run_command({'dbStats' => 1});
	print  "PUTVAL $host/mongostat/gauge-$dbstats->{db}_Collections N:$dbstats->{collections}\n";
	print  "PUTVAL $host/mongostat/gauge-$dbstats->{db}_File_Size N:$dbstats->{fileSize}\n";
	print  "PUTVAL $host/mongostat/gauge-$dbstats->{db}_Storage_Size N:$dbstats->{storageSize}\n";
	#print  "    db_$dbstats->{db}_nsSizeMB:  $dbstats->{nsSizeMB}\n";
	print  "PUTVAL $host/mongostat/gauge-$dbstats->{db}_Objects N:$dbstats->{objects}\n";
	print  "PUTVAL $host/mongostat/gauge-$dbstats->{db}_Index_Size N:$dbstats->{indexSize}\n";
	print  "PUTVAL $host/mongostat/gauge-$dbstats->{db}_Data_Size N:$dbstats->{dataSize}\n";
	print  "PUTVAL $host/mongostat/gauge-$dbstats->{db}_Indexes N:$dbstats->{indexes}\n";
}
##To find QPS and other db stats with mongostat
my @QPS_RAW = `mongostat -n1`;
#print Dumper @QPS_RAW;
#Trimming wach line output by removing leading and trailing white space
my $trim_var1 = $QPS_RAW[1];
$trim_var1 =~ s/^\s+|\s+$//g;
my $trim_var2 = $QPS_RAW[2];
$trim_var2 =~ s/^\s+|\s+$//g;
##Read each word in each line to an element in an array
my @stats_keys=split(/ +/, $trim_var1);
#print Dumper @stats_keys;
my @stats_values=split(/ +/, $trim_var2);
#print Dumper @stats_values;
my %stats_final;
##Map 2 lines of output to a hash
@stats_final{@stats_keys} = @stats_values;
#print Dumper \%stats_final;
my $insert = $stats_final{insert};
##Remove special char * from the output for yaml parsing
$insert =~ s/\*//g;
my $query = $stats_final{query};
$query =~ s/\*//g;
my $update = $stats_final{update};
$update =~ s/\*//g;
my $delete = $stats_final{delete};
$delete =~ s/\*//g;
my $faults = $stats_final{faults};
$faults =~ s/\*//g;
#print "$insert, $query, $update, $delete\n ";

my $result = $dbadmin->run_command({serverStatus => 1});
print  "PUTVAL $host/mongostat/gauge-Current_Connections N:$result->{connections}->{current}\n";
print  "PUTVAL $host/mongostat/gauge-Resident_Memory N:$result->{mem}->{resident}\n";
print  "PUTVAL $host/mongostat/gauge-Memory_Mapped N:$result->{mem}->{mapped}\n";
print  "PUTVAL $host/mongostat/gauge-Memory_Virtual N:$result->{mem}->{virtual}\n";
print  "PUTVAL $host/mongostat/gauge-Background_Flushes N:$result->{backgroundFlushing}->{flushes}\n";
print  "PUTVAL $host/mongostat/gauge-Background_Flushes_Total_ms N:$result->{backgroundFlushing}->{total_ms}\n";
#print $stat "  Insert: $result->{opcounters}->{insert}\n";
#print $stat "  Query: $result->{opcounters}->{query}\n";
print  "PUTVAL $host/mongostat/gauge-QPS N:$query\n";
print  "PUTVAL $host/mongostat/gauge-Faults N:$faults\n";
print  "PUTVAL $host/mongostat/gauge-Inserts N:$insert\n";
#print $stat "  Update: $result->{opcounters}->{update}\n";
print  "PUTVAL $host/mongostat/gauge-Update N:$update\n";
print  "PUTVAL $host/mongostat/gauge-Delete N:$delete\n";
print  "PUTVAL $host/mongostat/gauge-Command N:$result->{opcounters}->{command}\n";
##Since the keys are more than the values in %stats_final, the key is not idx miss, but db##
print  "PUTVAL $host/mongostat/gauge-Index_Miss_Percent N:$stats_final{db}\n";

$result = $dbadmin->run_command({replSetGetStatus => 1});
#$result = $dbadmin->run_command({'listCommands' => 1});
#$result = $dbadmin->run_command({'top' => 1});
#$result = $dbadmin->run_command({'dbStats' => 1});
#$result = $dbadmin->run_command({'whatsmyuri' => 1});
#print Dumper $result;
#print "  $result->{db}\n";
#print "  $result->{collections}\n";

#foreach my $repl ( @{$result->{members}} ) {
#if ($repl->{stateStr} eq "PRIMARY") {

#print join('_', split (':', "  $repl->{name}")), "_state_Is_primary: 1\n";
#}
#else{
#print  join('_', split (':', "  $repl->{name}")), "_state_Is_primary: 0\n";
#}
#}

}
