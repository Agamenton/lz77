#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>



#define ARG_COUNT 3
#define ARG_COMPRESS "-c"
#define ARG_DECOMPRESS "-d"
#define ARG_INPUT "input"

#define TRUE 1
#define FALSE 0

#define EXTENSION ".lz77"

#define MAX_WINDOW 510


typedef unsigned char 	byte;
typedef byte bool;
typedef enum {
	S_OFFSET,
	S_LENGTH,
	S_DATA,
} decode_state;

long long max(long long a, long long b);
long long min(long long a, long long b);
void print_args_help();


int main(int argc, char** argv)
{
    char* mode = NULL;
    char* input_p = NULL;

    // --------------------------
    // ---- Argument handler ----   // TODO: -w to specify window width

    // always 3 arguments
    if(argc != ARG_COUNT)
    {
        printf("count\n");
        print_args_help();
        return 1;
    }

    // dont mix '-c' and '-d'
    if((strcmp(argv[1], ARG_COMPRESS)==0 && strcmp(argv[2], ARG_DECOMPRESS)==0) || 
    (strcmp(argv[2], ARG_COMPRESS)==0 && strcmp(argv[1], ARG_DECOMPRESS)==0))
    {
        printf("mix\n");
        print_args_help();
        return 1;
    }

    // parse arguments
    for(int i = 1; i < ARG_COUNT; i++)
    {
        if(strcmp(argv[i], ARG_COMPRESS)==0)
        {
            mode = ARG_COMPRESS;
        }
        else if(strcmp(argv[i], ARG_DECOMPRESS)==0)
        {
            mode = ARG_DECOMPRESS;
        }
        else
        {
            input_p = argv[i];
        }
    }

    if(mode == NULL || input_p == NULL)
    {
        printf("|ERR| Failed to parse input arguments.\n");
        return 1;
    }
    // --------------------------


    // Open input file
    FILE* input_f = fopen(input_p, "rb");
    if(input_f == NULL)
    {
        printf("|ERR| Failed to open the input file: %s\n", input_p);
        return 1;
    }

    // Get how many bytes needed
    fseek(input_f, 0, SEEK_END);
    size_t file_size = ftell(input_f);
    fseek(input_f, 0, SEEK_SET);

    // allocate bytes for INput
    byte* input = (byte*)malloc(file_size);
    if(input == NULL)
    {
        printf("|ERR| Failed to allocate (input) memory for: %zu Bytes\n", file_size);
        fclose(input_f);
        return 1;
    }

    // read all bytes from file into memory
    if(fread(input, 1, file_size, input_f) != file_size)
    {
        printf("|ERR| Failed to read all bytes from input file\n");
        fclose(input_f);
        free(input);
        return 1;
    }

    // input file no longer needed
    fclose(input_f);


    // allocate bytes for OUTput
    int output_alloc_cnt = 1;
    size_t output_size = file_size;
    byte* output = (byte*)malloc(output_size);
    if(output == NULL)
    {
        printf("|ERR| Failed to allocate (output) memory for: %zu Bytes\n", output_size);
        free(input);
        return 1;
    }

    // output file is prepared here, so it can be closed uniformly,
    // but has different paths depending whether compressing or decompressing
    char* output_p = NULL;
    FILE* output_f = NULL;  


    // --------------------------
    // --- CORE FUNCTIONALITY ---
    int window_size = MAX_WINDOW;   // TODO: if -w argument
    if(window_size % 2)
    {
        window_size += 1;
    }

    if(window_size > MAX_WINDOW)
    {
        window_size = MAX_WINDOW;
    }

    // ENCODE / COMPRESS
    if(strcmp(mode, ARG_COMPRESS)==0)
    {
        clock_t start_time, end_time;
        double elapsed_time;

        start_time = clock();

        printf("Original size: %zu\n", file_size);
        // Create path for output file
        output_p = (char*)malloc(strlen(input_p) + strlen(EXTENSION));
        strcpy(output_p, input_p);
        strcat(output_p, EXTENSION);

        
        int look_ahead = (int)(window_size / 2);    
        size_t back_search = (int)(window_size / 2);
        
        long one_percent = (long)(file_size / 100);
        double current_percent = 0;
        size_t read_idx = 0;
        size_t output_idx = 0;

        byte offset = 0;
        byte length = 0;
        byte data = 0;
        bool debug = FALSE;
		bool real_data = TRUE;	// FALSE only used in one special case
        // for each currently read symbol
        while (read_idx < file_size)
        {
            //current_percent = (double)((double)read_idx / (double)one_percent);
            //printf("(%f/100\%)\r", current_percent);

            offset = 0;
            length = 0;
            data = input[read_idx];
			
			long long j = max(read_idx - back_search, 0);
            while(j < read_idx)
            {
                int current_length = 0;
                size_t current_search_idx = j;
				
				int test = input[j + current_length] == input[read_idx + current_length] ? 55 : 1;

                // if the current front end of the window is the same pattern as the current back
                while((read_idx + current_length < file_size) && 
                (current_length < look_ahead) &&
                (current_search_idx < read_idx) &&
                (input[j + current_length] == input[read_idx + current_length]))
                {
                    current_length += 1;
                    current_search_idx += 1;
                }

                if(current_length > length)
                {
                    offset = read_idx - j;
                    length = current_length;
                    data = input[min(read_idx + length, file_size - 1)];

                    // special case scenario if the last match is perfectly at the end of the file, so no next byte exists
                    if(read_idx + length == file_size)
                    {
                        data = 0;
						real_data = FALSE;
                    }
                }
                j += 1;
            }

            // if needed, re-alloc output data array
            if(output_idx > output_size - 3)
            {
                output_alloc_cnt += 1;
				output_size = output_size*output_alloc_cnt;
                output = (byte*)realloc(output, output_size);
                if(output == NULL)
                {
                    printf("|ERR| Failed to re-allocate (output) memory for: %zu Bytes\n", output_size*output_alloc_cnt);
                    free(input);
                    free(output);
                    free(output_p);
                    return 1;
                }
            }

            output[output_idx++] = offset;
            output[output_idx++] = length;
			if (real_data)
			{
				output[output_idx++] = data;				
			}

            read_idx += length + 1;
        }

        end_time = clock();
        elapsed_time = ((double) (end_time - start_time)) / CLOCKS_PER_SEC;
        printf("Time elapsed: %0.2f seconds\n", elapsed_time);
        printf("Encoded size: %zu", output_idx);

        output_f = fopen(output_p, "wb");
        if(output_f == NULL)
        {
            printf("|ERR| Failed to open/create output file: %s\n", output_p);
            free(input);
            free(output);
            free(output_p);
            return 1;
        }

        fwrite(output, 1, output_idx, output_f);
    }
    // DECODE / DECOMPRESS
    else
    {
		clock_t start_time, end_time;
        double elapsed_time;

        start_time = clock();

        printf("Original size: %zu\n", file_size);
        // Create path for output file
        output_p = "decoded.txt";	// TODO: input name minus extension (if extension == .lz77)
		
		decode_state state = S_OFFSET;
        byte offset = 0;
        byte length = 0;
        byte data = 0;
		size_t offset_start = 0;
		size_t offset_end = 0;
		
		size_t output_idx = 0;
		size_t read_idx = 0;
		while (read_idx < file_size)
		{
			
			byte read = input[read_idx];
			switch(state)
			{
				case S_OFFSET:
					offset = read;
					state = S_LENGTH;
					break;
				case S_LENGTH:
					length = read;
					state = S_DATA;
					break;
				case S_DATA:
					// if needed, re-alloc output data array
					if(output_idx > output_size - length - 1)
					{
						output_alloc_cnt += 1;
						output_size = output_size*output_alloc_cnt;
						output = (byte*)realloc(output, output_size);
						printf("realloced\n");
						if(output == NULL)
						{
							printf("|ERR| Failed to re-allocate (output) memory for: %zu Bytes\n", output_size*output_alloc_cnt);
							free(input);
							free(output);
							free(output_p);
							return 1;
						}
					}
					
					// if length and offset aren't 0 then append previous data
					if ((length != 0) && (offset != 0))
					{
						offset_start = output_idx - offset;	// DEV-NOTE: might be +1
						offset_end = offset_start + length;
						for (size_t i = offset_start; i < offset_end; i++)
						{
							output[output_idx++] = output[i];
						}
					}
					output[output_idx++] = read;
					length = 0;
					offset = 0;
					state = S_OFFSET;					
					break;					
			}
			read_idx++;
		}
		printf("\n");
		
		// special case when the last byte isn't available (because encoding ended with a pattern)
		if ((length != 0) && (offset != 0))
		{
			offset_start = output_idx - offset;	// DEV-NOTE: might be +1
			offset_end = offset_start + length;
			for (size_t i = offset_start; i < offset_end; i++)
			{
				output[output_idx++] = output[i];
			}
		}
		
        end_time = clock();
        elapsed_time = ((double) (end_time - start_time)) / CLOCKS_PER_SEC;
        printf("Time elapsed: %0.2f seconds\n", elapsed_time);
        printf("Decoded size: %zu", output_idx);
		
		output_f = fopen(output_p, "wb");
        if(output_f == NULL)
        {
            printf("|ERR| Failed to open/create output file: %s\n", output_p);
            free(input);
            free(output);
            free(output_p);
            return 1;
        }

        size_t written = fwrite(output, 1, output_idx, output_f);
    }

    fclose(output_f);
    free(input);
    free(output);
    free(output_p);

    return 0;
}


void print_args_help()
{
        printf("Wrong usage of arguments!\n\
Usage: lz77.o [-c] [-d] INPUT\n\
INPUT:\tRelative or full path to the input file you want to compress/decompress\n\
-c:\tChoose this to compress the input file\n\
-d:\tChoose this to de-compress a .lz77 file\n\
(you cannot use -c and -d together)");
}



long long max(long long a, long long b)
{
	if (a > b)
	{
		return a;
	}
	return b;
}

long long min(long long a, long long b)
{
	if (a < b)
	{
		return a;
	}
	return b;
}
