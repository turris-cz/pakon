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

FLOW2 ="""<flow type="destroy">
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
