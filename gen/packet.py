from gen.tcpip import get_ethernet_frame, get_ip_packet, get_tcp_stream, \
    get_openflow_header
from of10.parser import process_ofp_type
from of13.parser import process_ofp_type13
import gen.prints
import of10.prints
import gen.filters
import of13.prints


IP_PROTOCOL = 8
TCP_PROTOCOL = 6
TCP_FLAG_PUSH = 8
OF_HEADER_SIZE = 8


class OFMessage:
    '''
        Used to all all data regarding an OpenFlow message
    '''
    def __init__(self, pkt):
        self.main_packet = pkt
        self.packet = pkt.this_packet
        self.of_h = {}
        self.of_body = {}
        self.printing_seq = []
        self.offset = 0
        self.print_options = self.main_packet.print_options
        self.sanitizer = self.main_packet.sanitizer

    def seq_of_print(self, function):
        self.printing_seq.append(function)

    def process_openflow_header(self):
        self.of_h = get_openflow_header(self.packet, self.offset)
        self.offset += 8
        self.packet = self.packet[8:]

    def handle_malformed_pkts(self):
        string = ('!!! MalFormed Packet - Packet Len: %s Informed: %s '
                  'Missing: %s Bytes - Probably Reached MTU? !!!' %
                  (len(self.packet), self.of_h['length'],
                   self.of_h['length'] - len(self.packet)))
        message = {'message': string}
        self.prepare_printing('print_string', message)

    def process_openflow_body(self):
        self.process_openflow_header()
        if self.of_h['version'] is 1:
            try:
                if not process_ofp_type(self):
                    # of10.prints.print_type_unknown(self)
                    return 0
                return 1
            except:
                self.handle_malformed_pkts()
                return -1
        if self.of_h['version'] is 4:
            try:
                if not process_ofp_type13(self):
                    # of10.prints.print_type_unknown(self)
                    return 0
                return 1
            except:
                self.handle_malformed_pkts()
                return -1
        return 0

    def prepare_printing(self, string, values):
        self.of_body[string] = values
        self.seq_of_print(string)

    def print_packet(self, pkt):
        if not gen.filters.filter_OF_type(self):
            if pkt.printed_header is False:
                gen.prints.print_headers(pkt)
                pkt.printed_header = True
            gen.prints.print_openflow_header(self.of_h)
            if self.of_h['version'] is 1:
                of10.prints.print_body(self)
            elif self.of_h['version'] is 4:
                of13.prints.print_body(self)
            print


class Packet:
    '''
        Used to save all data about the packet
    '''
    def __init__(self, packet, print_options, sanitizer, ctr):
        # Raw packet
        self.packet = packet

        # Controls
        self.position = ctr
        self.offset = 0
        self.openflow_packet = False
        self.qtd_of_msg = 1
        self.cur_msg = 0
        self.printed_header = False

        # Filters
        self.print_options = print_options
        self.sanitizer = sanitizer

        # TCP/IP header
        self.l1 = {}
        self.l2 = {}
        self.l3 = {}
        self.l4 = {}

        # OpenFlow messages Array
        # As multiple OpenFlow messages per packet is support
        # an array needs to be created
        self.ofmsgs = []

    # Header TCP/IP
    def process_header(self, captured_size, truncated_size, now):
        self.process_l1(captured_size, truncated_size, now)
        self.process_l2()
        if self.l2['protocol'] == IP_PROTOCOL:
            self.process_l3()
            if self.l3['protocol'] == TCP_PROTOCOL:
                self.process_l4()
                if self.l4['flag_psh'] == TCP_FLAG_PUSH:
                    self.openflow_packet = True

    def process_l1(self, captured_size, truncated_size, now):
        self.l1 = {'caplen': captured_size, 'truncate_len': truncated_size,
                   'time': now}

    def process_l2(self):
        self.l2 = get_ethernet_frame(self.packet)
        self.offset = self.l2['length']

    def process_l3(self):
        self.l3 = get_ip_packet(self.packet, self.offset)
        self.offset += self.l3['length']

    def process_l4(self):
        self.l4 = get_tcp_stream(self.packet, self.offset)
        self.offset += self.l4['length']

    def get_remaining_bytes(self):
        return self.l1['caplen'] - self.offset

    def get_of_message_length(self):
        of_h = get_openflow_header(self.packet, self.offset)
        return of_h['length']

    # OpenFlow messages
    @property
    def of_h(self):
        return self.ofmsgs[self.cur_msg].of_h

    @property
    def of_body(self):
        return self.ofmsgs[self.cur_msg].of_body

    def process_openflow_messages(self):
        self.remaining_bytes = self.get_remaining_bytes()
        while (self.remaining_bytes >= 8):
            # self.this_packet is the OpenFlow message
            # let's remove the current OpenFlow message from the packet
            length = self.get_of_message_length()
            if length < 8:
                # MalFormed Packet
                return 0
            self.this_packet = self.packet[self.offset:self.offset+length]
            # Instantiate the OpenFlow message in the ofmsgs array
            # Process the content, using cur_msg position of the array of msgs
            self.ofmsgs.insert(self.cur_msg, OFMessage(self))
            version = self.ofmsgs[self.cur_msg].process_openflow_body()
            if version is 0:
                return 0
            elif version is -1:
                break
            self.remaining_bytes -= length
            self.offset += length
            # If there is another OpenFlow message, instantiate another OFMsg
            if (self.remaining_bytes >= 8):
                self.cur_msg += 1
                self.qtd_of_msg += 1

        return 1

    def print_packet(self):
        if not gen.filters.filter_OF_version(self):
            for msg in self.ofmsgs:
                msg.print_packet(self)
