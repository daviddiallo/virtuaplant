#!/usr/bin/env python

#########################################
# Imports
#########################################
# - Logging
import  logging

# - Twisted 
from twisted.internet.protocol  import ServerFactory

# - OPC-UA protocol
from opcua  import Client, Server, ua

#########################################
# Logging
#########################################
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

#########################################
# OPC-UA code
#########################################
# Global Variables
OPCUA_PORT = 4840

class OpcuaException(Exception):
    ''' Base OPC-UA exception '''

    def __init__(self, string):
        ''' Initialize the exception
        :param string: The message to append to the error
        '''
        self.string = string

    def __str__(self):
        return 'OPC-UA Error: %s' % self.string

class ConnectionException(OpcuaException):
    ''' Error resulting from a bad connection '''

    def __init__(self, string=""):
        ''' Initialize the exception
        :param string: The message to append to the error
        '''
        message = "[Connection] %s" % string
        OpcuaException.__init__(self, message)

class ClientOpcua(Client):
    def __init__(self, address, port = OPCUA_PORT):
        super(ClientOpcua, self).__init__("opc.tcp://localhost:4840/freeopcua/server/")
        self.connect()

    def read(self, addr):
        return self.readln(addr, 1)[0]

    def readln(self, addr, size):
        try:
            root = self.get_root_node()
    
            # Now getting a variable node using its browse path
            context = root.get_child(["0:Objects", "2:context"])
            log.debug("Context is: <%s>", context.get_value())
            
            return context.get_value()[addr:addr+size]
            
        except:
            raise ConnectionException

    def write(self, addr, data):
        try:
            root = self.get_root_node()
    
            # Now getting a variable node using its browse path
            context = root.get_child(["0:Objects", "2:context"])
            
            # Get context and modify it
            store = context.get_value()
            store[addr] = data
            
            context.set_value(store)
            
        except:
            raise ConnectionException

    def writeln(self, addr, data, size):
        try:
            root = self.get_root_node()
    
            # Now getting a variable node using its browse path
            context = root.get_child(["0:Objects", "2:context"])
            
            # Get context and modify it
            store = context.get_value()
            store[addr:addr+size] = data
            
            context.set_value(store)
            
        except:
            raise ConnectionException

class ServerOpcua(ServerFactory):
    '''
    Builder class for a opc-ua server
    This also holds the server datastore so that it is
    persisted between connections
    '''
    def __init__(self, address, port = OPCUA_PORT):
        # Setup OPC-UA Server
        self.opcua = Server()
        self.opcua.set_endpoint("opc.tcp://localhost:4840/freeopcua/server/")
        self.idx = self.opcua.register_namespace("http://examples.freeopcua.github.io")
        store = [0] * 100
        
        # get Objects node, this is where we should put our custom stuff
        objects = self.opcua.get_objects_node()
        
        # populating our address space
        self.context = objects.add_variable(self.idx, "context", store)
        self.context.set_writable()

    def startFactory(self):
        # Start OPC-UA Server
        self.opcua.start()

        # Stop Factory Server
        ServerFactory.startFactory(self)

    def stopFactory(self):
        # Stop OPC-uA Server
        self.opcua.stop()

        # Stop Factory Server
        ServerFactory.stopFactory(self)
 
    def write(self, addr, data):
        # Get current context
        store = self.context.get_value()
        
        # Write new value at addr
        store[addr] = data
        
        # Store new context
        self.context.set_value(store)
    
    def writeln(self, addr, data, size):
        # Get current context
        store = self.context.get_value()
        
        # Write new values from addr
        store[addr:addr+size] = data
        
        # Store new context
        self.context.set_value(store)
    
    def read(self, addr):
        return self.context.get_value()[addr]

    def readln(self, addr, size):
        return self.context.get_value()[addr:addr+size]

if __name__ == '__main__':
    sys.exit(main())
