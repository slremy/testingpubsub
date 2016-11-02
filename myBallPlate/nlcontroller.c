//version 3 : the below code is working fine for reading the data, it reads the data from model(HTTP base (webpy)) but I should complete below items:
// 		saving the data to file
//		running the SIGNAL to call the controlState Function
//		Check the running data and confirm that the code does what is suppose to do
//version 4 : it is working, but the X is not updating correctly
//version 5 : strcmp was used wrong and fixed

#include <string.h>
#include <unistd.h>
#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <signal.h>
#include <sys/time.h>
#include <curl/curl.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <time.h>			//for new clock (clock_gettime)




#define BUFLEN 1024
#define NPACK 10

//Simulation parameters
double h;//Simulation timestep  //please change the value to modify the intervals!!!
double dur;//Simulation duration
int clientport = 0 ;
char *clientname ;
char *network ;
char *host;
int port;
char *suffix ;
char filename[128] ;
FILE *fobj;
char url[1024];
char temp_base_url[1024] ;
double mydata[14];
int timer, interrupt;

CURL *curl = NULL;

//Control reference settings
double max_angle =3.14/180.0*(32+20) ; //Max roll/pitch angle reference for both axes controller
double max_torque = 20;
char *ykernel = "butterfly2";
double yamplitude = 2.0;
double yfrequency = 1.0/100.00;
char *xkernel = "butterfly1";
double xamplitude = 2.0;
double xfrequency = 1.0/100.00;

//Global variables updated in control loop
double X[3],Y[3],THETA[3],PHI[3],u_x,u_y, AR, BR, AM, BM;

int iteration = 0; //Keep track of loop iterations
double mse_x = 0; //Mean squared error in x
double mse_y = 0; //Mean squared error in y
double tcrash = INFINITY; //Time the program crashed. If it didn't crash, this is infinite
typedef enum { False, True } bool;
bool crashed = False;//If the program crashed

double t1 = 0;
double t0;

double sign(double input)
{
	if (input > 0) return 1;
	else if (input == 0) return 0;
	else return -1;
}

//Reference function -- gets reference at a time t
double ref(double t,char *kernel,double amplitude,double frequency)
{
    
	double _temp = -1;
	if (strcmp(kernel ,"butterfly1") == 0)
	{
		_temp = amplitude* cos(2*M_PI*t*frequency) * sin(4*M_PI*t*frequency);
	}
	else if (strcmp(kernel,"butterfly2") ==0)
	{
        _temp =  amplitude* cos(2*M_PI*t*frequency) * sin(2*M_PI*t*frequency);
	}
	else if (strcmp(kernel, "step") == 0)
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
	else if (strcmp(kernel, "sin") == 0)
	{
		_temp =  amplitude * sin(frequency*2*M_PI*t);
	}
	else if (strcmp(kernel, "cos") == 0)
	{
		_temp =  amplitude * cos(frequency*2*M_PI*t);
	}
	//printf("\ncounter: %d	-t: %.9lf		-kernel: %s		-ref: %.9lf",counter,t,kernel,_temp);
	return _temp;
}

typedef struct {
    char *contents;
    int size;
} data;

//microsecond clock - used up to version 6
double uclock(){
    struct timeval tv;   // see gettimeofday(2)
    gettimeofday(&tv, NULL);
    double t = (double) tv.tv_sec + (double) tv.tv_usec/1000000.0;
    return(t);
}

//For UDP Client
void diep(char *s)
{
	perror(s);
    //exit(1);
}

typedef struct {
    char *contents;
    int size;
} curldata;

/*Curl uses this function to write the contents of a webpage to a file/stdout*/
size_t write_data( void *ptr, size_t size, size_t nmeb, void *stream)
{
    data *curl_output = (data *)stream;
    int curl_output_size = size * nmeb;
    
    curl_output->contents = (char *) realloc(curl_output->contents, curl_output->size + curl_output_size + 1);
    if (curl_output->contents) {
        memcpy(curl_output->contents, ptr, curl_output_size); /*Copying the contents*/
        curl_output->size += curl_output_size;
        curl_output->contents[curl_output->size] = 0;
    }
    return curl_output_size;
}


int uprocess(char server_ip[15], int server_port,char* get)
{
	// Get string and send to server_ip (assumes IPv4)
    int n=0;
    char garbage;
    CURLcode res = -1;

    if(curl) {
        curldata s;
        s.contents = (char *)malloc(1);
        s.size = 1;
        
        char modurl[1024];
        snprintf(modurl, 1024, "http://%s:%d%s",server_ip,server_port,get);
        //printf("Sent URL: %s\n",modurl);
        curl_easy_setopt(curl, CURLOPT_URL, modurl);
        // perform write function to get data
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &s);
        // Perform the request, res will get the return code 
        res = curl_easy_perform(curl);
        // Check for errors
        if(res != CURLE_OK)
            fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
        if (s.size > 1){
            n = sscanf(s.contents, "[%lf %lf %lf %lf %lf]%c",mydata,mydata+1,mydata+2,mydata+3,mydata+4, &garbage);
        }else{
            int count;
            for (count=0;count < 14; count++)
                mydata[count]=0;
        }
        free(s.contents);
    }
    else {
        printf("Could not communicate @ %lf\n", t1);
    }
    return n;				//in version 6 : changed to: n from: strlen(recvline) because: it returned zero instead of 60ish
}

//#################################################################################
//The main control loop
//void controlState(signum, _){
void controlState(){
    double angle_d,angle_d1,ct;
    double x_d, y_d, e_x, e_y;
    int response = 0;
    double tr;
    
    // Update the time and iteration number
    iteration += 1;
    t1 = uclock() - t0 ;
    
    // Send control inputs via web service call
    snprintf(url, sizeof url,"/u?&value0=%.4f&value1=%.4f&t=%.6f&]",u_x,u_y,t1);
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
        fprintf(fobj,"%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\t%.6f\n" ,ct,X[0],Y[0],THETA[0],PHI[0],t1,x_d,y_d,angle_d,angle_d1,mse_x,mse_y,u_x,u_y,tr,ct);   //$$ remained
    }
    else 
    {
        printf("Communication timed out at %lf!!", clock() - t0);
    }
}

void stopped(){
    //  Stop timer and plant
    printf("Stopping!\n");
    setitimer(timer, 0, 0);
    snprintf(url, sizeof url,"%s", "/init?]");
    uprocess(host,port,url);
    uprocess(host,port,url);
    exit(0);
}    

int main(int argc, char *argv[]) {
    
    struct itimerval value;
    double duration,h,KpR,KiR,KdR,KpM,KiM,KdM;
        
    //	Take arguments to determine file name, port, etc.
    if (argc > 3)
    {

        clientname = argv[1];
        network = argv[2];
        host = argv[3];
        port = atoi(argv[4]);
        suffix = argv[5];
        printf( "Running: nlcontroller_current %s %s %s %d %s", clientname, network, host, port, suffix);
        
        if (argc > 6)	duration = strtof(argv[6],0);
        else			duration = .35;
        
        if (argc > 7)	h = strtof(argv[7],0);
        else			h = .02;
        
        if (argc > 8)	KpR = strtof(argv[8],0);
        else			KpR = -.312-1;
        
        if (argc > 9)	KiR = strtof(argv[9],0);
        else			KiR = 0;
        
        if (argc >  10)	KdR = strtof(argv[10],0);
        else			KdR = 1.299;
        
        if (argc > 11)	KpM = strtof(argv[11],0);
        else			KpM = 5.79;
        
        if (argc > 12)	KiM = strtof(argv[12],0);
        else			KiM = 0;
        
        if (argc > 13)	KdM = strtof(argv[13],0);
        else			KdM = .22;
        
        printf( "Running: %lf, %lf, %lf, %lf, %lf, %lf, %lf, %lf\n", duration,h,KpR,KiR,KdR,KpM,KiM,KdM);
        
        //	Setting the signal's interval
        value.it_interval.tv_sec = 0;	//the running interval by second
        value.it_interval.tv_usec = (h*1000000)+1;	//the running interval by microseconds
        value.it_value.tv_sec = 0;			//when it start by second
        value.it_value.tv_usec = (h*1000000)+1;	//when it start by microseconds
        
        //	Log data to the correct file
        snprintf(filename,sizeof filename,"curl%s_%s_%s.txt",clientname, network, suffix);
        printf("\nLogging data to %s\n", filename);
        fobj = fopen(filename, "w");
        
        AR= KpR;
        BR= KdR/h;
        
        AM= KpM;
        BM= KdM/h;

        t0 = uclock();

        curl = curl_easy_init();
        curl_easy_setopt(curl, CURLOPT_TIMEOUT_MS, 150);
        curl_easy_setopt(curl, CURLOPT_NOSIGNAL, 1);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_data);

        
        //	Reset plant state
        snprintf(url, sizeof url,"%s","/init?]");
        uprocess(host,port,url);				// included
        uprocess(host,port,url);
        
        u_x= u_y= 0;
        //timer=ITIMER_PROF; interrupt=SIGPROF;
        timer=ITIMER_REAL; interrupt=SIGALRM;
        signal(interrupt, controlState);
        setitimer(timer, &value, 0);
        signal (SIGINT, stopped);
        
        //	Stop program after duration
        while (t1 < duration && crashed == False);	
        
        //  Stop timer and plant
        setitimer(timer, 0, &value);
        snprintf(url, sizeof url,"%s", "/init?&]");
        uprocess(host,port,url);
        uprocess(host,port,url);
        fclose(fobj);
        // always cleanup
        curl_easy_cleanup(curl);

        
    }
    else{
        printf( "\nUsage: nlcontroller_current %s %s %s %s %s\n", "clientname", "network", "host", "port", "suffix");
        exit(1);
    }
    return 0;
}

