% Author: Jawshan Ara Shatil
%Date finalized: 03.06.2025

clear;
directory='/Users/shatil/Library/CloudStorage/Box-Box/VEDB_IN/Good_data/angular_vel_data';
folder= ["2022_02_09_13_40_13", "2022_06_24_11_41_06", "2022_06_24_11_49_03", "2022_06_24_14_26_28", "2022_09_15_15_25_58", "2022_09_19_11_27_04", "2022_10_06_15_51_11"];
HeadCal_Time_title = {'Session_ID' 'Angular Velocity ID' 'MaxFFT start time' 'MaxFFT end time' 'First Shake Start Time' 'First Shake End Time'};
Timestamp_save = 'First_HeadCal_time_FFTm.xlsx';  
writecell(HeadCal_Time_title,Timestamp_save);

for i = 1:7
    folder_name = folder(i);
    for n=0:1
        N=int2str(n);
        filename = strcat(directory, '/',folder_name, '_', 'ang_vel_', N, '.xlsx');
        filenameT=strcat(directory,'/',folder_name, '_', 'timestamp.xlsx');
        timestamp = readtable(filenameT);
        Time=table2array(timestamp);
        Time = Time(2:end);
        ang_vel = readtable(filename);
        ang_vel=table2array(ang_vel);
        ang_vel=ang_vel(2:end);
        
        acceptable_index = min(length(Time),length(ang_vel));
        
        %% sampling frequency
        Fs=floor(acceptable_index/Time(acceptable_index)); 

        %% FFT for angular velocity 
        z=zeros([5*Fs 1]); %5s window
        window_size = 5; %in seconds
        sliding_width= 1; %in seconds
        counter=floor(((length(ang_vel) -(window_size*Fs))/(sliding_width*Fs)))+1;
        dataset_complex_magnitude =[];
        dataset_absFFT = [];
        for N=1:counter
            x_start=floor((N-1)*(sliding_width*Fs)+1); 
            
            x_end=floor((N-1)*(sliding_width*Fs)+(window_size*Fs));
                if x_end > length(ang_vel)
                    x_end = length(ang_vel);
                end
        %% windowing the signal
            z=ang_vel(x_start:x_end);
            x = 0:length(z)-1; 
            L = length(x);     
            samp_rate = Fs;    
            freqx = 0:samp_rate/L:(samp_rate-samp_rate/L);            
            window_fft = fft(z);
            %single sided FFT, amplitude of the real value
            P2 = abs(window_fft/L);
            P1 = P2(1:L/2+1);
            P1(2:end-1) = 2*P1(2:end-1);
            f = Fs/L*(0:(L/2));
        
            absFFT=P1;
            dataset_absFFT = cat(2,dataset_absFFT,absFFT);
        
        
        end
   
    max_absFFT_dataset=max(dataset_absFFT);
    max_All = max(dataset_absFFT,[],"all");
    acceptable_absFFT=(max_All*2)/3;
    
    [i_row_shake,i_col_shake] =find(max_absFFT_dataset> acceptable_absFFT);
    [i_row_max,i_col_max] =find(max_absFFT_dataset == max_All);
    
    
    %% Finding the window of the max and first head shake
    
    max_x_start=floor((i_col_max)*(sliding_width*Fs)); 
    max_x_end=floor((i_col_max)*(sliding_width*Fs)+(window_size*Fs));
    
    shake_x_start=floor((i_col_shake)*(sliding_width*Fs)); 
    shake_x_end=floor((i_col_shake)*(sliding_width*Fs)+(window_size*Fs));
    
    max_window_start_time = Time(max_x_start);
    max_window_end_time = Time(max_x_end);
    
    shake_window_start_time = Time(shake_x_start);
    number_shake_present=length(shake_window_start_time);
    shake_window_end_time = Time(shake_x_end);
    
    HeadCal_Time = [folder_name, n, num2str(max_window_start_time), num2str(max_window_end_time), num2str(shake_window_start_time(1)), num2str(shake_window_end_time(1))];
    writematrix(HeadCal_Time,Timestamp_save, 'WriteMode','append')
    end

end
%plot(Time(1:acceptable_index), ang_vel(1:acceptable_index))
    
