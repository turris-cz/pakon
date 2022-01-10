FLOW1 = """<flow type="new">
    <meta direction="original">
        <layer3 protonum="2" protoname="ipv4">
            <src>192.168.16.40</src>
            <dst>192.168.16.255</dst>
        </layer3>
        <layer4 protonum="17" protoname="udp">
            <sport>60308</sport>
            <dport>21027</dport>
        </layer4>
    </meta>
    <meta direction="reply">
        <layer3 protonum="2" protoname="ipv4">
            <src>192.168.16.255</src>
            <dst>192.168.16.40</dst>
        </layer3>
        <layer4 protonum="17" protoname="udp">
            <sport>21027</sport>
            <dport>60308</dport>
        </layer4>
    </meta>
    <meta direction="independent">
        <timeout>30</timeout>
        <id>1657073971</id>
        <unreplied/>
    </meta>
</flow>"""

FLOW2 = """<flow type="destroy">
    <meta direction="original">
        <layer3 protonum="2" protoname="ipv4">
            <src>192.168.122.1</src>
            <dst>192.168.122.255</dst>
        </layer3>
        <layer4 protonum="17" protoname="udp">
            <sport>60308</sport>
            <dport>21027</dport>
        </layer4>
        <counters>
            <packets>1</packets>
            <bytes>648</bytes>
        </counters>
    </meta>
    <meta direction="reply">
        <layer3 protonum="2" protoname="ipv4">
            <src>192.168.122.255</src>
            <dst>192.168.122.1</dst>
        </layer3>
        <layer4 protonum="17" protoname="udp">
            <sport>21027</sport>
            <dport>60308</dport>
        </layer4>
        <counters>
            <packets>0</packets>
            <bytes>0</bytes>
        </counters>
    </meta>
    <meta direction="independent">
        <id>1043691933</id>
        <unreplied/>
    </meta>
</flow>"""

FLOW3 = """<flow type="new">
    <meta direction="original">
        <layer3 protonum="2" protoname="ipv4">
            <src>192.168.122.1</src>
            <dst>192.168.122.255</dst>
        </layer3>
        <layer4 protonum="17" protoname="udp">
            <sport>60308</sport>
            <dport>21027</dport>
        </layer4>
    </meta>
    <meta direction="reply">
        <layer3 protonum="2" protoname="ipv4">
            <src>192.168.122.255</src>
            <dst>192.168.122.1</dst>
        </layer3>
        <layer4 protonum="17" protoname="udp">
            <sport>21027</sport>
            <dport>60308</dport>
        </layer4>
    </meta>
    <meta direction="independent">
        <timeout>30</timeout>
        <id>990802630</id>
        <unreplied/>
    </meta>
</flow>"""

FLOW4 = """<flow type="destroy">
    <meta direction="original">
        <layer3 protonum="2" protoname="ipv4">
            <src>172.20.6.206</src>
            <dst>172.20.6.255</dst>
        </layer3>
        <layer4 protonum="17" protoname="udp">
            <sport>60308</sport>
            <dport>21027</dport>
        </layer4>
        <counters>
            <packets>1</packets>
            <bytes>648</bytes>
        </counters>
    </meta>
    <meta direction="reply">
        <layer3 protonum="2" protoname="ipv4">
            <src>172.20.6.255</src>
            <dst>172.20.6.206</dst>
        </layer3>
        <layer4 protonum="17" protoname="udp">
            <sport>21027</sport>
            <dport>60308</dport>
        </layer4>
        <counters>
            <packets>0</packets>
            <bytes>0</bytes>
        </counters>
    </meta>
    <meta direction="independent">
        <id>3170238355</id>
        <unreplied/>
    </meta>
</flow>"""

FLOW5 = """<flow type="new">
    <meta direction="original">
        <layer3 protonum="2" protoname="ipv4">
            <src>192.168.168.250</src>
            <dst>74.6.143.26</dst>
        </layer3>
        <layer4 protonum="1" protoname="icmp"></layer4>
    </meta>
    <meta direction="reply">
        <layer3 protonum="2" protoname="ipv4">
            <src>74.6.143.26</src>
            <dst>192.168.168.250</dst>
        </layer3>
        <layer4 protonum="1" protoname="icmp"></layer4>
    </meta>
    <meta direction="independent">
        <timeout>30</timeout>
        <id>2056000897</id>
        <unreplied/>
    </meta>
</flow>"""


FLOW6 = """<flow type="destroy">
	<meta direction="original">
		<layer3 protonum="2" protoname="ipv4">
			<src>192.168.168.250</src>
			<dst>216.58.201.78</dst>
		</layer3>
		<layer4 protonum="1" protoname="icmp"></layer4>
		<counters>
			<packets>5</packets>
			<bytes>420</bytes>
		</counters>
	</meta>
	<meta direction="reply">
		<layer3 protonum="2" protoname="ipv4">
			<src>216.58.201.78</src>
			<dst>192.168.168.250</dst>
		</layer3>
		<layer4 protonum="1" protoname="icmp"></layer4>
		<counters>
			<packets>5</packets>
			<bytes>420</bytes>
		</counters>
	</meta>
	<meta direction="independent">
		<id>2350446838</id>
	</meta>
</flow>"""

FLOW7 = """<flow type="destroy"><meta direction="original"><layer3 protonum="2" protoname="ipv4"><src>10.0.0.139</src><dst>52.98.152.178</dst></layer3><layer4 protonum="6" protoname="tcp"><sport>57812</sport><dport>443</dport></layer4><counters><packets>10</packets><bytes>1140</bytes></counters></meta><meta direction="reply"><layer3 protonum="2" protoname="ipv4"><src>52.98.152.178</src><dst>192.168.168.250</dst></layer3><layer4 protonum="6" protoname="tcp"><sport>443</sport><dport>57812</dport></layer4><counters><packets>6</packets><bytes>2409</bytes></counters></meta><meta direction="independent"><id>439469702</id><assured/></meta></flow>"""

JSON1 = """{
  "flow": {
    "meta": [
      {
        "layer3": {
          "src": "192.168.16.40",
          "dst": "192.168.16.255",
          "protonum": "2",
          "protoname": "ipv4"
        },
        "layer4": {
          "sport": 60308,
          "dport": 21027,
          "protonum": "17",
          "protoname": "udp"
        },
        "direction": "original"
      },
      {
        "layer3": {
          "src": "192.168.16.255",
          "dst": "192.168.16.40",
          "protonum": "2",
          "protoname": "ipv4"
        },
        "layer4": {
          "sport": 21027,
          "dport": 60308,
          "protonum": "17",
          "protoname": "udp"
        },
        "direction": "reply"
      },
      {
        "timeout": 30,
        "id": 1657073971,
        "unreplied": "",
        "direction": "independent"
      }
    ],
    "type": "new"
  }
}"""

JSON2 = """{
  "flow": {
    "meta": [
      {
        "layer3": {
          "src": "192.168.122.1",
          "dst": "192.168.122.255",
          "protonum": "2",
          "protoname": "ipv4"
        },
        "layer4": {
          "sport": 60308,
          "dport": 21027,
          "protonum": "17",
          "protoname": "udp"
        },
        "counters": {
          "packets": 1,
          "bytes": 648
        },
        "direction": "original"
      },
      {
        "layer3": {
          "src": "192.168.122.255",
          "dst": "192.168.122.1",
          "protonum": "2",
          "protoname": "ipv4"
        },
        "layer4": {
          "sport": 21027,
          "dport": 60308,
          "protonum": "17",
          "protoname": "udp"
        },
        "counters": {
          "packets": 0,
          "bytes": 0
        },
        "direction": "reply"
      },
      {
        "id": 1043691933,
        "unreplied": "",
        "direction": "independent"
      }
    ],
    "type": "destroy"
  }
}"""

JSON3 = """{
  "flow": {
    "meta": [
      {
        "layer3": {
          "src": "192.168.122.1",
          "dst": "192.168.122.255",
          "protonum": "2",
          "protoname": "ipv4"
        },
        "layer4": {
          "sport": 60308,
          "dport": 21027,
          "protonum": "17",
          "protoname": "udp"
        },
        "direction": "original"
      },
      {
        "layer3": {
          "src": "192.168.122.255",
          "dst": "192.168.122.1",
          "protonum": "2",
          "protoname": "ipv4"
        },
        "layer4": {
          "sport": 21027,
          "dport": 60308,
          "protonum": "17",
          "protoname": "udp"
        },
        "direction": "reply"
      },
      {
        "timeout": 30,
        "id": 990802630,
        "unreplied": "",
        "direction": "independent"
      }
    ],
    "type": "new"
  }
}"""

JSON4 = """{
  "flow": {
    "meta": [
      {
        "layer3": {
          "src": "172.20.6.206",
          "dst": "172.20.6.255",
          "protonum": "2",
          "protoname": "ipv4"
        },
        "layer4": {
          "sport": 60308,
          "dport": 21027,
          "protonum": "17",
          "protoname": "udp"
        },
        "counters": {
          "packets": 1,
          "bytes": 648
        },
        "direction": "original"
      },
      {
        "layer3": {
          "src": "172.20.6.255",
          "dst": "172.20.6.206",
          "protonum": "2",
          "protoname": "ipv4"
        },
        "layer4": {
          "sport": 21027,
          "dport": 60308,
          "protonum": "17",
          "protoname": "udp"
        },
        "counters": {
          "packets": 0,
          "bytes": 0
        },
        "direction": "reply"
      },
      {
        "id": 3170238355,
        "unreplied": "",
        "direction": "independent"
      }
    ],
    "type": "destroy"
  }
}"""
