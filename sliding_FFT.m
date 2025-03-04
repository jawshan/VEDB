clear
clc

% read Data
Inputdirectory='/Users/shatil/Library/CloudStorage/Box-Box/VEDB_IN/VEDB/angular_vel_data';
folder_name= '2022_02_09_13_40_13';
filename0 = strcat(Inputdirectory, '/',folder_name, '_', 'ang_vel_0.xlsx');
%filename0=strcat(Inputdirectory, '/','2022_02_09_13_40_13_ang_vel_0.xlsx');
%filename1=strcat(Inputdirectory, '/','2022_02_09_13_40_13_ang_vel_1.xlsx');
filenameT=strcat(Inputdirectory,'/','2022_02_09_13_40_13_timestamp.xlsx');
%% prepping x and y axis for FFT

timestamp = readtable(filenameT);
Time=table2array(timestamp);

ang_vel0 = readtable(filename0);
ang_vel0=table2array(ang_vel0);

acceptable_index = length(ang_vel0);
%% calculating sampling frequency

%index_equal1= find(Time=1);
index_Time_less_than1 = find(Time<1 & Time>0.994); %intex_Time_less_than1
value_less_than1 =Time(index_Time_less_than1); %value_less_than1
index_Time_greater_than1 = find(Time<1.0007 & Time>1); % intex_Time_greater_than1
value_greater_than1 = Time(index_Time_greater_than1); %value_greater_than1
value_equal_1s=1;
%Fs = (index_Time_less_than1-1) + ((value_equal_1s - value_less_than1) / (value_greater_than1 - value_less_than1)) * (index_Time_greater_than1 - index_Time_less_than1);
%Fs= ceil(Fs);

Fs=floor(acceptable_index/Time(acceptable_index)); %sampling frequency, giving wrong values

%% Section 1.1: FFT for angular velocity 10s long window sliding with 4s window
%z=zeros([10*Fs 1]); %10s window
window_size = 5; %in seconds
sliding_width= 1; %in seconds
counter=floor(((length(ang_vel0) -(window_size*Fs))/(sliding_width*Fs)))+1;
dataset_complex_magnitude =[];
dataset_absFFT = [];
for n=1:counter
    x_start=fix((n-1)*(sliding_width*Fs)+1); %4s second of sliding 4*Fs
    x_end=fix((n-1)*(sliding_width*Fs)+(window_size*Fs));% 10s window length 10*Fs
%error management
     if x_end > length(ang_vel0)
         x_end = length(ang_vel0);
     end
%% windowing the signal
     z=ang_vel0(x_start:x_end);
    x = 0:length(z)-1; % number of collected data points 
    L = length(x);     % the length of the collected data points.
    samp_rate = Fs;    % the sampling rate of the eeg data file
    freqx = 0:samp_rate/L:(samp_rate-samp_rate/L);  % the signal frequency.            
    window_fft = fft(z);

%% complex magnitude
% abs_window_fft= abs(window_fft);
% dataset_complex_magnitude = cat(2,dataset_complex_magnitude,abs_window_fft);

% figure(n)
% plot(Fs/L*(0:L-1),abs_window_fft,"LineWidth",1)
% title("Complex Magnitude of fft Spectrum")
% xlabel("f (Hz)")
% ylabel("|fft(Angular velocity 0)|")

% visualization
% max_complexFFT_dataset=max(dataset_complex_magnitude);
% plot(max_complexFFT_dataset)
% xlim([1 counter]);

%% single sided FFT, amplitude of the real value
P2 = abs(window_fft/L);
P1 = P2(1:L/2+1);
P1(2:end-1) = 2*P1(2:end-1);
f = Fs/L*(0:(L/2));

% figure(n+2)
% plot(f,P1,"LineWidth",1) 
% title("Single-Sided Amplitude Spectrum of Angular velocity 0")
% xlabel("f (Hz)")
% ylabel("|P1(f)|")

absFFT=P1;
dataset_absFFT = cat(2,dataset_absFFT,absFFT);
% filename = 'FFTval.xlsx';
% writematrix(dataset_absFFT,filename)

%% visualization
max_absFFT_dataset=max(dataset_absFFT);
plot(max_absFFT_dataset)
xlim([1 counter]);


end

max_absFFT_dataset=max(dataset_absFFT);
max_All = max(dataset_absFFT,[],"all");
[i_row_max,i_col_max] =find(max_absFFT_dataset == max_All);

%Finding the window of the max

max_x_start=fix((i_col_max-1)*(sliding_width*Fs)+1); %4s second of sliding 4*Fs
max_x_end=fix((i_col_max-1)*(sliding_width*Fs)+(window_size*Fs));% 10s window length 10*Fs

max_window_number = i_col_max
max_window_start_time = Time(max_x_start)
max_window_end_time = Time(max_x_end)

