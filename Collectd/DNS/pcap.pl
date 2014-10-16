#!/usr/bin/perl
use strict;
use warnings;
use Data::Dumper;
use Net::Pcap::Easy;
$| = 1; ##Disable block buffering
    my $npe = Net::Pcap::Easy->new(
        dev              => "eth0", #Change to your active interface where bind listens.
        filter           => "port 53 and (udp)",
        packets_per_loop => 100,
        bytes_to_capture => 1024,
        timeout_in_ms    => 0, # 0ms means forever
        promiscuous      => 0, # true or false

);
1 while defined
    # NOTE: defined, since loop returns 0 and undef on error

    $npe->loop( sub {
	my ($user_data, $header, $raw_bytes) = @_;
	#print Dumper @_;

#print %{$header};
        # $header is like this:
        # { caplen => 96, len => 98, tv_sec => 1245963414, tv_usec => 508250 },

#my $query = unpack("H*", $raw_bytes);
my $ip = substr $raw_bytes, 26, 4; ##Getting source IP 8 bytes.

#my $destination = substr $raw_bytes, 30, 4;
print (($header->{tv_sec}),":",(join '_',unpack("C*", $ip)),"\n");#"->",(join '.',unpack("C*", $destination)),"\n");


    });
