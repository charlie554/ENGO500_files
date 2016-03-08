#include<iostream>
#include<vector>
#include<sstream>
#include<fstream>
#include<stdio.h>
#include<stdlib.h>
#include<string>
#include<unistd.h>
//usleep()
void intSpeed();
void adc();
void temp();
void upload(int streamID, double value);
void upload(int streamID, std::string value);
void ip();

int dstream=156964;
int ustream=249072;
int adc1stream=249162;
int tstream=249156;
int ipstream=258735;
//string dir = "/home/pi/ENGO500_files/";

using namespace std;
int main()
{
	usleep(5000000);
	ip();
//	system("cd /home/pi/ENGO500_files");
	int timer = 12;
	while(1)
	{
		intSpeed();
		temp();
		adc();
/*		cout << endl << "waiting " << timer*5 << " seconds:" << endl;
		for(int i = 0 ; i <  timer ; i++)
		{
			usleep(5000000);
			cout << i*5+5 << "seconds have passed" << endl;
		}*/
		usleep(5000000);
		cout << endl;
	}
	return 0;

}

void intSpeed()
{
	cout << "starting speedtest-cli" << endl;
	system("python /home/pi/ENGO500_files/speedtest_cli.py > internet.txt");
	ifstream input;
	input.open("internet.txt");
	double down,up;
	string temp;
	while(!input.eof())
	{
		input >> temp;
		if(temp == "Download:")
			input >> down;
		if(temp == "Upload:")
			input >> up;
	}
	input.close();
	cout << "upload: " << up << "down: " << down << endl;
	cout << "uploading download speed" << endl;
	upload(dstream,down);
	cout << "uploading upload speed" << endl;
	upload(ustream,up);
	return;
}

void adc()
{
	system("python /home/pi/ENGO500_files/adc.py");
	ifstream input;
	input.open("adc.txt");
	double temp;
	double avg=0;
	vector<double> adc1;
	while(!input.eof())
	{
		input >> temp;
		adc1.push_back(temp);
	}
	for(int i = 0 ; i < adc1.size() ; i++)
	{
		avg += adc1[i];
	}
	avg=avg/adc1.size();
	upload(adc1stream,avg);
	input.close();
}

void temp()
{
	system("python /home/pi/ENGO500_files/temp.py");
	ifstream input;
	input.open("temp.txt");
	double t=0; //as in temperature
	double temp; //as in temporary
	vector<double> temps;
	while(!input.eof())
	{
		input >> temp;
		temps.push_back(temp);
	}
	for(int i = 0 ; i < temps.size() ; i++)
	{
		t=t+temps[i];
	}
	t = t/temps.size();
	upload(tstream,t);
	input.close();
}

void upload(int streamID, double value)
{
	stringstream convert1;
	stringstream convert2;
	convert1 << streamID;
	convert2 << value;

	string id = convert1.str();
	string val= convert2.str();
	string command;
	command =  "python /home/pi/ENGO500_files/upload.py " + id + " " + val;
	system(command.c_str());
	return;
}

void upload(int streamID, std::string value)
{
        stringstream convert1;
        //stringstream convert2;
        convert1 << streamID;
        //convert2 << value;

        string id = convert1.str();
        //string val= convert2.str();
        string command;
        command =  "python /home/pi/ENGO500_files/upload.py " + id + " " + value;
        system(command.c_str());
        return;
}


void ip()
{
	system("ifconfig > ip.txt");
	ifstream ipt;
	ipt.open("ip.txt");
	string temp,ipa;
	while(!ipt.eof())
	{
		ipt >> temp;
		if(temp == "wlan0")
		{
			ipt >> temp >> temp >>temp >>temp >> temp >> ipa;
		}
	}
	cout << "IP: " << ipa << endl << "Uploading" << endl;
	upload(ipstream,ipa);
}
