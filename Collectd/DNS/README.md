## The purpose of this script 

This was written to plot the dns queries using collectd. Enabling query logging lead to around 200% performance drop in bind9 even after finetuning because of the number of systemcalls it make (stat /etc/localtime, fstat, etc..). Making this independent from bind seems to have solved my issue, and successfully sniffed all packets at around 100000+ QPS. I wrote 2 scripts for this.

1. pcap.pl, which uses Net::Pcap::Easy to capture ethernet frames, filtered for UDP and port 53. This is not decoded with the builtin functions, as object oriented modules will slow packet analysing, and will lead to packet drops by this script after qps greater than 20,000. Instead, we use substring to get just the source IP raw data, unpacks it,  and epoch value of time when the packet recieved, and use IPC to pass it to the second script pcap.pl(Because writing to a file added latency, and to a unix namedpipe will require additional handlers to handle PIPE Exceptions.) which then aggregates this data, and sends the top 10 IPs, along with its QPS and the aggregated QPS to collectd. 
  1. Packages required: libpcap-dev
  2. Cpan Modules required: Net::Pcap::Easy
2. pcap_ipc.pl, that uses IPC to read data from pcap.pl, applies some filters, and iterates and sorts the data every second (with change in value of epoch ) and outputs top 10 IP, its qps and aggregate qps in collectd format.
  1. Packages required: None
  2. Modules required: Socket

##### Active interfaces and certain limits are hardcoded in the script, which may be changed.


-- nohupped@gmail.com
