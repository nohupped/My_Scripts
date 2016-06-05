package main

import (
	"io/ioutil"
	"fmt"
	"os"
	"encoding/json"
	"strings"
	"encoding/xml"
	"flag"
)



type TwoD [][]interface{}
type MainContainer struct {
	Devices []struct{
		Server struct{
			       Bu struct{
					  //Add_info bool `json:"add_info"`
					  TAG1 TwoD `json:"applications"`
					  TAG2 TwoD `json:"name"`
					  TAG3 []string `json:"owners"`
					  Users []string `json:"users"`
				  }
			       Hostname string `json:"name"`
			       Networksetup struct{
					  Primary_ip string `json:"primary_ip"`
				  }`json:"network_setup"`
		       } `json:"server"`

	} `json:"devices"`
}

type Project struct {
	XMLName xml.Name `xml:"project"`
//	Version string   `xml:"version,attr"`
	Nodes []Node `xml:"node"`
}
type Node struct {
	Name        string `xml:"name,attr"`
	Tag         string `xml:"tag,attr"`
	Description string `xml:"description,attr"`
	Hostname    string `xml:"hostname,attr"`
	OsArch      string `xml:"osArch,attr"`
	OsFamily    string `xml:"osFamily,attr"`
	OsName      string `xml:"osName,attr"`
	OsVersion   string `xml:"osVersion,attr"`
	Username    string `xml:"username,attr"`
	Keypath     string `xml:"ssh-key-storage-path,attr"`
}
func (N *Node) Make_Custom(M *struct{ Server struct{ Bu struct{ TAG1 TwoD "json:\"applications\""; TAG2 TwoD "json:\"name\""; TAG3 []string "json:\"owners\""; Users []string "json:\"users\"" }; Hostname string "json:\"name\""; Networksetup struct{ Primary_ip string "json:\"primary_ip\"" } "json:\"network_setup\"" } "json:\"server\"" }, user, keypath *string) {
	N.Name = M.Server.Hostname
	var tmpdata []string
	for _, i := range M.Server.Bu.TAG1 {
		tmpdata = append(tmpdata, i[0].(string))
	}
	for _, i := range M.Server.Bu.TAG2 {
		tmpdata = append(tmpdata, i[0].(string))
	}
	for _, i := range M.Server.Bu.TAG3 {
		tmpdata = append(tmpdata, i)
	}
	N.Tag = strings.Replace(strings.Join(tmpdata, ","), " ", "_", -1)
	N.Description = M.Server.Hostname
	switch M.Server.Networksetup.Primary_ip {
	case "":
		N.Hostname = M.Server.Hostname
	case "None":
		N.Hostname = M.Server.Hostname
	default:
		N.Hostname = M.Server.Networksetup.Primary_ip
	}
	N.OsArch = "NA"
	N.OsFamily = "NA"
	N.OsName = "NA"
	N.OsVersion = "NA"
	N.Username = *user
	N.Keypath = *keypath
}


func main() {
	user := flag.String("user", "foo", "ssh user")
	keypath := flag.String("keypath", "keys/foo/bar", "Path to ssh key")
	jsonconf := flag.String("json", "keys/foo/bar", "Path to json file from runbook")
	flag.Parse()

	//jsonfile, err  := ioutil.ReadFile("/home/girishg/search.json.bak")
	jsonfile, err  := ioutil.ReadFile(*jsonconf)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}



	var jsonobject MainContainer
	json.Unmarshal(jsonfile, &jsonobject)

	Proj := &Project{}
	//var nodes []node
	for _, i := range jsonobject.Devices {
		var node Node
		node.Make_Custom(&i, user, keypath)
		//nodes = append(nodes, node)

		Proj.Nodes = append(Proj.Nodes, node)

	}
//	fmt.Printf("%v\n", Proj)
	output, _ := xml.MarshalIndent(Proj, "  ", "    ")
	os.Stdout.Write([]byte(xml.Header))
	os.Stdout.Write(output)


}
