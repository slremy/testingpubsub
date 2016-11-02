import java.util.Date;
import java.util.Timer;

import java.util.TimerTask;
import java.util.Formatter;

import java.net.*;
import java.io.*;


public class nlcontrollerudp extends TimerTask{
    
    //Simulation parameters
    static double h;//Simulation timestep  //please change the value to modify the intervals!!!
    static double dur;//Simulation duration in ms
    
    int clientport = 0 ;
    String clientname;
    String network;
    String host;
    int port;
    String suffix;
    String myfilename;
    File thefile;
    Formatter fobj;
    
    double[] mydata = new double[]{0,0,0,0,0};
    
    DatagramSocket clientSocket;
    
    //Control reference settings
    double max_angle =3.14/180.0*(32+20) ; //Max roll/pitch angle reference for both axes controller
    double max_torque = 20;
    String ykernel = "butterfly2";
    double yamplitude = 2.0;
    double yfrequency = 1.0/100.00;
    String  xkernel = "butterfly1";
    double xamplitude = 2.0;
    double xfrequency = 1.0/100.00;

    //Global variables updated in control loop
    double X[] = new double[]{0,0,0}; 
    double Y[] = new double[]{0,0,0};
    double THETA[] = new double[]{0,0,0};
    double PHI[] = new double[]{0,0,0};
    double u_x,u_y, AR, BR, AM, BM;

    int iteration = 0; //Keep track of loop iterations
    double mse_x = 0; //Mean squared error in x
    double mse_y = 0; //Mean squared error in y
    double tcrash = Double.POSITIVE_INFINITY; //Time the program crashed. If it didn't crash, this is infinite
    boolean crashed =false;//If the program crashed
    
    double t1 = 0;
    double t0 = 0;
    
    public double sign(double input)
    {
        if (input > 0) return 1;
        else if (input == 0) return 0;
        else return -1;
    }
    
    public double fmod(double input,double range)
    {
        return input % range;
    }
    
    public double ref(double t, String kernel, double amplitude, double frequency)
    {
        double _temp = -1;
        if (kernel == "butterfly1")
        {
            _temp = amplitude* Math.cos(2*Math.PI*t*frequency) * Math.sin(4*Math.PI*t*frequency);
        }
        else if (kernel == "butterfly2")
        {
            _temp =  amplitude* Math.cos(2*Math.PI*t*frequency) * Math.sin(2*Math.PI*t*frequency);
        }
        else if (kernel == "step")
        {
            if (t < 0)
            {
                _temp =  0.0;
            }
            else
            {
                _temp =  amplitude;
            }
        }
        else if (kernel == "sin")
        {
            _temp =  amplitude * Math.sin(2*Math.PI*t*frequency);
        }
        else if (kernel == "cos")
        {
            _temp =  amplitude * Math.cos(2*Math.PI*t*frequency);
        }
        //printf("\ncounter: %d	-t: %.9lf		-kernel: %s		-ref: %.9lf",counter,t,kernel,_temp);
        return _temp;
    }
    
    public double uclock()
    {
        return new Date().getTime()/1000.0;
    }
    
    public int uprocess(String server_ip, int port, String control_action)
    {
        String[] data = new String[100];
        int datalen=0;
        try {
            
            InetAddress IPAddress = InetAddress.getByName(server_ip);
            byte[] sendData = new byte[1024];
            byte[] receiveData = new byte[1024];
            //String sentence = inFromUser.readLine();
            sendData = control_action.getBytes();
            DatagramPacket sendPacket = new DatagramPacket(sendData, sendData.length, IPAddress, port);
            clientSocket.send(sendPacket);
            
            DatagramPacket receivePacket = new DatagramPacket(receiveData, receiveData.length);
            clientSocket.receive(receivePacket);
            String inputLine = new String(receivePacket.getData());

            data = inputLine.split("\\[")[1].split("\\]")[0].split(" ");
            if (data.length != mydata.length) {
                datalen = 0;
            }
            else {
                datalen = data.length;
                for (int i = 0; i < datalen; i++) {
                    mydata[i]=Double.parseDouble(data[i]);
                }
            }
        } catch (Exception e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }

        return datalen;
    }

    //#################################################################################
    //The main control loop
    //void controlState(signum, _)
    public void controlState(){

        double angle_d,angle_d1,ct;
        double x_d, y_d, e_x, e_y;
        int response = 0;
        double tr;
    
        // Update the time and iteration number
        iteration += 1;
        t1 = uclock() - t0 ;
        String url;
                
        // Send control inputs via web service call
        url=String.format("/u?&value0=%.4f&value1=%.4f&t=%.6f&]",u_x,u_y,uclock()-t0);
        
        response = uprocess(host,port,url);
        tr = uclock() - t0;
        if (response != 0){
                X[2]=X[1];X[1]=X[0];X[0]=mydata[0];
                Y[2]=Y[1];Y[1]=Y[0];Y[0]=mydata[1];
                THETA[2]=THETA[1];THETA[1]=THETA[0];THETA[0]=mydata[2];
                PHI[2]=PHI[1];PHI[1]=PHI[0];PHI[0]=mydata[3];
                ct = mydata[4];

                //Compute the references and errors for position controller
                x_d = ref(t1,xkernel,xamplitude,xfrequency);
                e_x = x_d - X[0];
                y_d = ref(t1,ykernel,yamplitude,yfrequency);
                e_y = y_d - Y[0];

                //compute control inputs for the position controller
                angle_d = AR * (e_x) + BR * (X[0]-X[1]);
        
                if (angle_d > max_angle) angle_d=max_angle; 
                else if (angle_d < -max_angle) angle_d=-max_angle; 
                u_x = AM*(angle_d*16 - THETA[0]) + BM * (THETA[0] - THETA[1]);
                
                angle_d1 = AR * (e_y) + BR * (Y[0]-Y[1]);
        
                if (angle_d1 > max_angle) angle_d1=max_angle; 
                else if (angle_d1 < -max_angle) angle_d1=-max_angle; 
                u_y = AM*(angle_d1*16 - PHI[0]) + BM * (PHI[0] - PHI[1]);
                
                //Update the performance parameters
                mse_x = (mse_x * iteration + e_x*e_x)/(iteration + 1);
                mse_y = (mse_y * iteration + e_y*e_y)/(iteration + 1);

                fobj.format("%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\n" ,ct,X[0],Y[0],THETA[0],PHI[0],t1,x_d,y_d,angle_d,angle_d1,mse_x,mse_y,u_x,u_y,tr,ct);   //$$ remained
                fobj.flush();
                
        }
        else {
            System.out.format("Communication timed out at %g!!", uclock() - t0);
        }
    }
    
    public nlcontrollerudp(String args[]){
        String temp_base_url;
        double KpR,KiR,KdR,KpM,KiM,KdM;
        
        //Confirm the supplied program parameters, and create the filename
        clientname = args[0];
        network = args[1];
        host = args[2];
        port = Integer.parseInt(args[3]);
        suffix = args[4];

        if (args.length > 5)   dur = Float.parseFloat(args[5]);
        else                   dur = .35;
        
        if (args.length > 6)   h = Float.parseFloat(args[6]);
        else                    h = .02;
        
        if (args.length > 7)   KpR = Float.parseFloat(args[7]);
        else                    KpR = -.312-1;
        
        if (args.length > 8)   KiR = Float.parseFloat(args[8]);
        else                    KiR = 0;
        
        if (args.length >  9) KdR = Float.parseFloat(args[9]);
        else                    KdR = 1.299;
        
        if (args.length > 10)  KpM = Float.parseFloat(args[10]);
        else                    KpM = 5.79;
        
        if (args.length > 11)  KiM = Float.parseFloat(args[11]);
        else                    KiM = 0;
        
        if (args.length > 12)  KdM = Float.parseFloat(args[12]);
        else                    KdM = .22;

        AR= KpR;
        BR= KdR/h;
        
        AM= KpM;
        BM= KdM/h;

        temp_base_url=String.format("http://%s:%d",host,port);        
        String myfilename;
        myfilename=String.format("judp%s_%s_%s.txt",clientname, network, suffix);
        System.out.format( "\nLogging data to %s\n", myfilename);
        try {
            
            thefile = new File(myfilename);
            fobj = new Formatter(thefile);
            
        }
        catch (FileNotFoundException e) {
            e.printStackTrace();
        }

        try{
            clientSocket = new DatagramSocket();
            clientSocket.setSoTimeout(150);
        } catch (Exception e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }

    }
    
    public void init(){
        String request;
        //	Reset plant state
        t0 = uclock();        
        request=String.format("%s", "/init?]");
        uprocess(host,port,request);				
        uprocess(host,port,request); 
    }
    
    //String url;
    @Override
    public void run() {
    	controlState();
    }
    
    public static void main(String args[]) throws Exception{
        
        
        //	Take arguments to determine file name, port, etc.
        if (args.length > 4)
        {
            nlcontrollerudp controller = new nlcontrollerudp(args);
            //create timer task as daemon thread
            Timer timer = new Timer(true);
            try {
                controller.init();                
                //start the calculate control code on the interval timer
                timer.scheduleAtFixedRate(controller, 0, (int)(h*1000)); // <<--interval is set to h milliseconds
                //cancel after sometime
                Thread.sleep((int)(dur*1000));
            }
            catch (InterruptedException e) {
                e.printStackTrace();
            }
            
            System.out.format("Stopping!\n");
            timer.cancel();
            controller.init();
            
        }
        else{
            System.out.format( "\nUsage: nlcontrollerudp %s %s %s %s %s\n", "clientname", "network", "host", "port", "suffix");
        }
    }
}



