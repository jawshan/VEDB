clear
clc

% read Data
Inputdirectory='/Users/shatil/Library/CloudStorage/Box-Box/VEDB_IN/Good_data/angular_vel_data';
%folder_name= '2022_02_09_13_40_13';
folder= ["2022_06_24_11_41_06","2022_02_09_13_40_13", "2022_06_24_11_49_03", "2022_06_24_14_26_28", "2022_09_15_15_25_58", "2022_09_19_11_27_04", "2022_10_06_15_51_11"];

HeadCal_Time_title = {'Folder_name' 'Angular velocity#' 'Start_time' 'End_time'};
for i = 1:7
    folder_name = folder(i);
    for n=0:1
        N=int2str(n);
        filename = strcat(Inputdirectory, '/',folder_name, '_', 'ang_vel_', N, '.xlsx');
        filenameT=strcat(Inputdirectory,'/',folder_name, '_', 'timestamp.xlsx');
%% prepping x and y axis for FFT

        timestamp = readtable(filenameT);
        Time=table2array(timestamp);        
        ang_vel = readtable(filename);
        ang_vel=table2array(ang_vel);
        
        %acceptable_index = length(ang_vel);
        

        Time_cap=find(Time>299.999 & Time<300.006);
        Time=Time(1:Time_cap(1));
        ang_vel=ang_vel(1:Time_cap(1));
        acceptable_index = Time_cap(1);
        
        %% calculating sampling frequency

        Fs=floor(acceptable_index/Time(acceptable_index)); 

%% Section 1.1: FFT for angular velocity 10s long window sliding with 4s window
%z=zeros([10*Fs 1]); %10s window
        window_size = 5; %in seconds
        sliding_width= 1; %in seconds
        counter=floor(((length(ang_vel) -(window_size*Fs))/(sliding_width*Fs)))+1;
        dataset_complex_magnitude =[];
        dataset_absFFT = [];
        for N=1:counter
                x_start=floor((N-1)*(sliding_width*Fs)+1); %4s second of sliding 4*Fs
                
                x_end=floor((N-1)*(sliding_width*Fs)+(window_size*Fs));% 10s window length 10*Fs
        %error management
             if x_end > length(ang_vel)
                 x_end = length(ang_vel);
             end
        %% windowing the signal
                z=ang_vel(x_start:x_end);
                x = 0:length(z)-1; % number of collected data points 
                L = length(x);     % the length of the collected data points.
                samp_rate = Fs;    % the sampling rate of the eeg data file
                freqx = 0:samp_rate/L:(samp_rate-samp_rate/L);  % the signal frequency.            
                window_fft = fft(z);
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
        
%         %% visualization
%             figure(n+1)
%             max_absFFT_dataset=max(dataset_absFFT);
%             plot(max_absFFT_dataset)
%             xlim([1 counter]);
        
        
        end
   
max_absFFT_dataset=max(dataset_absFFT);
max_All = max(dataset_absFFT,[],"all");
[i_row_max,i_col_max] =find(max_absFFT_dataset == max_All);

%Finding the window of the max

max_x_start=floor((i_col_max-1)*(sliding_width*Fs)); %4s second of sliding 4*Fs
max_x_end=floor((i_col_max-1)*(sliding_width*Fs)+(window_size*Fs));% 10s window length 10*Fs

max_window_number = i_col_max;
max_window_start_time = Time(max_x_start);
max_window_end_time = Time(max_x_end);


HeadCal_Time(1)= folder_name;
HeadCal_Time(2)= n;
HeadCal_Time(3)= max_window_start_time;
HeadCal_Time(4)= max_window_end_time;
C = [HeadCal_Time_title; num2cell(HeadCal_Time)];

resultdirectory='/Users/shatil/Library/CloudStorage/Box-Box/VEDB_IN/VEDB';

Timestamp_save = 'HeadCal_time.xlsx';
writecell(C,Timestamp_save, 'WriteMode','append')
    end
plot(Time(1:acceptable_index), ang_vel(1:acceptable_index))
end

