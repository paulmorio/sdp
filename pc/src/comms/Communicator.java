package comms;
/**
 * Simple class to send and receive data over serial.
 * @author Chris
 */


import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.IOException;
import java.util.Enumeration;
import java.util.Scanner;
import gnu.io.CommPortIdentifier;   // RXTX library at https://github.com/rxtx/rxtx
import gnu.io.SerialPort;
import gnu.io.SerialPortEvent;
import gnu.io.SerialPortEventListener;


public class Communicator implements SerialPortEventListener {
    SerialPort serialPort;
    /** The serial port we're going to use, differs across platforms **/
    private static final String PORT_NAMES[] = {
            "/dev/tty.usbmodem000001",  // Mac OS X
            "/dev/tty.ACM0"    // Linux? (TODO)
    };

    private BufferedReader input;
    private OutputStream output;
    /** Milliseconds to block while waiting for port open **/
    private static final int TIME_OUT = 2000;
    /** Default bits per second for COM port **/
    private static final int DATA_RATE = 9600;

    public void initialize() {
        CommPortIdentifier portID = null;
        Enumeration portEnum = CommPortIdentifier.getPortIdentifiers();

        // Find a serial port matching one of the items in PORT_NAMES
        while (portEnum.hasMoreElements()) {
            CommPortIdentifier currPortID = (CommPortIdentifier) portEnum.nextElement();
            for (String portName : PORT_NAMES) {
                if (currPortID.getName().equals(portName)) {
                    portID = currPortID;
                    break;
                }
            }
        }

        if (portID == null) {
            System.out.println("Could not find COM port.");
            return;
        }

        try {
            // Open serial port with the class name as the application name
            serialPort = (SerialPort) portID.open(this.getClass().getName(), TIME_OUT);
            // Set parameters
            serialPort.setSerialPortParams(DATA_RATE, SerialPort.DATABITS_8, SerialPort.STOPBITS_1,
                                            SerialPort.PARITY_NONE);
            // Open IO streams
            input = new BufferedReader(new InputStreamReader(serialPort.getInputStream()));
            output = serialPort.getOutputStream();

            // Add event listeners
            serialPort.addEventListener(this);
            serialPort.notifyOnDataAvailable(true);
        } catch (Exception e) {
            System.err.println(e.toString());
        }
    }

    /** Remove event listener and close serial port. Call this when you're done to prevent port locking. */
    public synchronized void close() {
        if (serialPort != null) {
            serialPort.removeEventListener();
            serialPort.close();
        }
    }

    public void write(int i) {
        try {
            output.write(i);
        } catch (IOException e) {
            System.err.println(e.toString());
        }
    }
    /** Handle an event on the serial port. Read the data and print (currently) **/
    public synchronized void serialEvent(SerialPortEvent s) {
        if (s.getEventType() == SerialPortEvent.DATA_AVAILABLE) {
            try {
                String inputLine = input.readLine();
                System.out.println(inputLine);
            } catch (Exception e) {
                System.err.println(e.toString());
            }
        }
    }
    
    public static void main (String[] args) {
        Communicator main = new Communicator();
        main.initialize();
        Thread t = new Thread() {
            public void run() {
                try {
                    synchronized(this) {
                        this.wait();
                    }
                } catch (InterruptedException e) {
                    System.err.println(e.toString());
                }
            }
        };
        t.start();

        System.out.printf("Started on port %s\n.", main.serialPort.getName());
        
        Scanner s = new Scanner(System.in);
        
        // Read an integer from console and send to arduino.
        while (true) {
            int in = Integer.parseInt(s.nextLine());
            main.write(in);
        }
    }
}
