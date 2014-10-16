#!/usr/bin/perl
use strict;
use warnings;
use Socket;
my %buf;
open(INCOMING,"/etc/collectd/pcap.pl |"); #Location of pcap.pl
my $hostname = `hostname -f`;
chomp $hostname;
my $hostname_formated = $hostname;
$hostname_formated =~ s/\./_/g;##For collectd formatting
my ($cur,$epoc,$source,$dest);

my ($name, $aliases, $addrtype, $length, @addrs) = gethostbyname ($hostname);
my $ip = join ("_", unpack('C4',$addrs[0])); ##Check self IP to exclude outbound requests and count only inbound requests.

my $query = <INCOMING>;
$epoc = substr($query,0,10) if defined $query;
my $c = 0;
#print "$epoc\n";
while (<INCOMING>) {
	#my $query = /(^[0-9].+)\-\>([0-9].*)\-\>([0-9].*)/;
	#$cur = $1;
	#$source = $2;
	$cur = substr($_,0,10); ##Using substring because it is faster than regex
	$source = substr($_,11,-1);
	if ($source ne $ip) {
		if ($epoc != $cur) {
			my $counter;
			foreach my $sort (sort {$buf{$b} <=> $buf{$a}} keys %buf ) {
				print "PUTVAL $hostname/dns-$sort/gauge N:$buf{$sort}\n";##Print per IP qps
				last if (++$counter == 10);##Increase if we need to plot more than top 10 IPs.
			}
			%buf = ();
			$epoc = $cur;
			print "PUTVAL $hostname/dns-$hostname_formated\_qps/gauge N:$c\n";##Print aggregated QPS
			$c=0;
		}
		$buf{$source}++;
		$c++;
	}
}
