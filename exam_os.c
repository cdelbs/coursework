#include <pthread.h>
#include <semaphore.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>
clock_t start_time, current_time;
int TIME_QUANTUM = 4;
clock_t cpustart, cpuend, schedulerstart,schedulerend, memstart, memend;
double cpu_time_used,scheduler_time_used, memory_time_used;

// Define core CPU registers
#define NUM_CORES 4
int PC[NUM_CORES] = {0};
int ACC[NUM_CORES] = {0};
int IR[NUM_CORES] = {0};
int PN[NUM_CORES] = {0};

#define MAX_PROCESSES 6
#define BUFFER_SIZE 5
#define NUM_THREADS 4

double waitTable[MAX_PROCESSES];// WaitingTime
double turnaroundTable[MAX_PROCESSES]; // turnaroundTime
double burstTable[MAX_PROCESSES];// burst times
double globalArrivals[MAX_PROCESSES]; //keep track of arrival times globally
void initTables() {
    //init timetables
   for (int i = 0; i < MAX_PROCESSES; i++) {
        turnaroundTable[i] = time(NULL);  // Store current clock time
        waitTable[i] = time(NULL);  // Store current clock time
        burstTable[i] = time(NULL);  // Store current clock time
    }
}


// Status flags
int CF[NUM_CORES] = {0};  // carry flag
int OF[NUM_CORES] = {0};  // overflow flag
int ZF[NUM_CORES] = {0};  // zero flag
int EF[NUM_CORES] = {0};  // error flag
int FF[NUM_CORES] = {0};  // finish flag

#define MAX_INTERRUPTS 4

//process control block
struct PCB {
    int pid;    // process ID
    int pc;     // program counter
    int acc;    // accummulator
    int state;  // Process state (0 = Ready, 1 = Running, 2 = Complete)
    int pri;    // Priority level
    int timeremaining; // remaining execution time for SRT
    int responseRatio; // for HRRN
    int arrivalTime;
    int burstTime;
};
void timerInterrupt(int core, struct PCB pcb[]);
void ioInterrupt(int core, struct PCB pcb[]);
void sysCallInterrupt(int core, struct PCB pcb[]);
void trapInterrupt(int core, struct PCB pcb[]);
// create IVT and interrupt types
void (*IVT[MAX_INTERRUPTS])();

enum { TIMER_INT, IO_INT, SYSCALL_INT, TRAP_INT };
void initIVT() {
    IVT[TIMER_INT] = timerInterrupt;
    IVT[IO_INT] = ioInterrupt;
    IVT[SYSCALL_INT] = sysCallInterrupt;
    IVT[TRAP_INT] = trapInterrupt;
}
// mutex for interrupt handling
pthread_mutex_t interrupt_mutex;

struct InterArgs {
    int core;
    struct PCB pcb[MAX_PROCESSES];
};
// int memory[256];
// Define cache and RAM sizes
#define L1_CACHE_SIZE 64
#define L2_CACHE_SIZE 128
#define RAM_SIZE 1025
// Define memory structures
int RAM[RAM_SIZE];
int L1Cache[L1_CACHE_SIZE][2];
int L2Cache[L2_CACHE_SIZE][2];
// Mutexes and semaphores for safe access
pthread_mutex_t memory_mutex;
// Structure for the Memory Table entry
struct CoreMemoryBlock {
    int core;
    int memoryStart;
    int memoryEnd;
    int isFree;  // 1 = free, 0 = allocated
};
// do - create a memo table
struct CoreMemoryBlock coreMemoryTable[NUM_CORES + 1];  // Example: divide RAM into blocks
// Function to initialize the Memory Table
void initCoreMemoryTable() {
    int c = RAM_SIZE / (NUM_CORES + 1);  // current block size
    int j = 0;                           // current RAM address
    // SHARED MEMORY

    for (int i = 0; i < NUM_CORES; i++) {
        coreMemoryTable[i].core = i;
        coreMemoryTable[i].memoryStart = j;
        coreMemoryTable[i].memoryEnd = (j + c) - 1;
        j += c;
        printf("Size of block %d = %d \n", i,
               (coreMemoryTable[i].memoryEnd - coreMemoryTable[i].memoryStart + 1));
    }
    coreMemoryTable[NUM_CORES].core = -1;  // last block shared
    coreMemoryTable[NUM_CORES].memoryStart =
        coreMemoryTable[NUM_CORES - 1].memoryEnd + 1;     // last block shared
    coreMemoryTable[NUM_CORES].memoryEnd = RAM_SIZE - 1;  // last block shared
}

// handle cache lookup
int cacheLookup(int address) {
    // do: Implement L1 and L2 cache lookup logic
    // check L1 cache first; if miss, check L2 cache; if both miss, access RAM
    // return data if found or load from RAM if not found
    //  Check L1:
    for (int i = 0; i < L1_CACHE_SIZE; i++) {
        if (L1Cache[i][0] == address) return L1Cache[i][1];
    }
    for (int i = 0; i < L2_CACHE_SIZE; i++) {
        if (L2Cache[i][0] == address) return L2Cache[i][1];
    }
    return RAM[address];
}
// determine if a address exists in the cache
int inCache(int address) {
    for (int i = 0; i < L1_CACHE_SIZE; i++) {
        if (L1Cache[i][0] == address) return i;
    }
    for (int i = 0; i < L2_CACHE_SIZE; i++) {
        if (L2Cache[i][0] == address) return i;
    }
    return -1;
}
// function to handle cache write policies (Write-Through or Write-Back)
void cacheWrite(int address, int data, int writePolicy) {
    // do: write data to cache and manage RAM updates based on write policy
    //  Write Through
    if (writePolicy == 0) {
        if (inCache(address) != -1) {  // is in cache already, update...
            if (L1Cache[inCache(address)][0] == address)
                L1Cache[inCache(address)][1] = data;
            else if (L2Cache[inCache(address)][0] == address)
                L2Cache[inCache(address)][1] = data;
            RAM[address] = data;
            return;
        }
        for (int i = 0; i < L1_CACHE_SIZE; i++) {
            if (L1Cache[i][0] <= 0) {
                L1Cache[i][0] = address;
                L1Cache[i][1] = data;
                RAM[address] = data;
                return;
            }
        }
        for (int i = 0; i < L2_CACHE_SIZE; i++) {
            if (L2Cache[i][0] <= 0) {
                L2Cache[i][0] = address;
                L2Cache[i][1] = data;
                RAM[address] = data;
                return;
            }
        }
        // Write Back
    } else if (writePolicy == 1) {
        if (inCache(address) != -1) {  // is in cache already, update...
            if (L1Cache[inCache(address)][0] == address)
                L1Cache[inCache(address)][1] = data;
            else if (L2Cache[inCache(address)][0] == address)
                L2Cache[inCache(address)][1] = data;
            return;
        }
        for (int i = 0; i < L1_CACHE_SIZE; i++) {
            if (L1Cache[i][0] <= 0) {
                L1Cache[i][0] = address;
                L1Cache[i][1] = data;
                return;
            }
        }
        for (int i = 0; i < L2_CACHE_SIZE; i++) {
            if (L2Cache[i][0] <= 0) {
                L2Cache[i][0] = address;
                L2Cache[i][1] = data;
                return;
            }
        }
    }
    // If cache full, update random address
    int randindex = rand() % L2_CACHE_SIZE;
    RAM[L2Cache[randindex][0]] = L2Cache[randindex][1];
    L2Cache[randindex][0] = address;
    L2Cache[randindex][1] = data;
}
// function for memory access with cache (includes semaphore protection)
int accessMemory(int address, int data, int isWrite) {
    pthread_mutex_lock(&memory_mutex);  // lock memory for exclusive access
    int result;
    if (isWrite) {
        cacheWrite(address, data, 0);  // use 1 for write-policy through policy in this example
        result = 0;
    } else {
        result = cacheLookup(address);  // fetch data from cache or RAM
    }
    pthread_mutex_unlock(&memory_mutex);  // unlock memory
    return result;
}

// Mutex for safe resource access
pthread_mutex_t memory_mutex;
// ISA operations
#define ADD 1
#define SUB 2
#define MUL 3
#define DIV 4
#define LOAD 5
#define STORE 6
#define AND 7
#define OR 8
#define JMP 9
#define JZ 10
#define LOCK 11
#define UNLOCK 12
#define YIELD 13
// add more based on the rquirements
// Function to initialize memory with sample instructions
//  load the program values into the memory and RAM
void loadProgram() {
    // Complete: Load sample instructions into memory
    // Eg:
    // memory[0] = LOAD; memory[1] = 10; //LOAD 10 into ACC
    // Add more instructions as needed
    //  CORE 0
    accessMemory(2, LOAD, 1);
    accessMemory(3, 10, 1);  // LOAD 10 to ACC
    accessMemory(4, ADD, 1);
    accessMemory(5, 8, 1);  // ADD 8 to ACC
    accessMemory(6, STORE, 1);
    accessMemory(7, 15, 1);  // STORE ACC to 15
    // CORE 2
    accessMemory(412, LOAD, 1);
    accessMemory(413, 3, 1);  // LOAD 3 to ACC
    accessMemory(414, MUL, 1);
    accessMemory(415, 2, 1);  // MUL 2 to ACC
    accessMemory(416, STORE, 1);
    accessMemory(417, 421, 1);  // STORE ACC to 421
}
// Function to simulate instruction fetching
void fetch(int core) {
    // Complete: Set the IR to the instruction at the current PC
    IR[core] = accessMemory(PC[core] + coreMemoryTable[core].memoryStart, 0, 0);
}
// Function to decode and execute the current instruction
void execute(int core) {
    // Complete: Decode and execute the instruction in IR
    // Implement cases for each instruction:
    //- ADD: Add a value to ACC
    //- SUB: Subtract a value from ACC
    //----------------
    int currentValue = accessMemory(coreMemoryTable[core].memoryStart + PC[core] + 1, 0,
                                    0);  //[core].memoryStart+PC[core]+1;
    printf("Core: %d , PC: %d, ACC: %d, IR: %d, DATA: %d \n", core, PC[core], ACC[core], IR[core],
           currentValue);

    switch (IR[core]) {
        case ADD:
            ACC[core] += currentValue;
            break;
        case SUB:
            ACC[core] -= currentValue;
            break;
        case MUL:
            ACC[core] *= currentValue;
            break;
        case DIV:
            ACC[core] /= currentValue;
            break;
        case LOAD:
            ACC[core] = currentValue;
            break;
        case STORE:
            accessMemory(currentValue, ACC[core], 1);
            break;
        case AND:
            ACC[core] = ACC[core] & currentValue;
            break;
        case OR:
            ACC[core] = ACC[core] | currentValue;
            break;
        case JMP:
            PC[core] = currentValue - 2;
            break;
        case JZ:
            if (ZF[core] == 1) PC[core] = currentValue - 2;
            break;
        case LOCK:
            pthread_mutex_lock(&memory_mutex);
            break;
        case UNLOCK:
            pthread_mutex_unlock(&memory_mutex);
            break;
        case YIELD:
            sleep(1);
    }
    PC[core] += 2;

    return;
}

// save the current states
void save_state(int pn, struct PCB pcb[], int core) {  // saves registers from current process
    pcb[pn].pid = pn;
    pcb[pn].pc = PC[core];
    pcb[pn].acc = ACC[core];
    if (pcb[pn].state != 2) {
        pcb[pn].state = 0;
    }

    return;
}
// load the current states
void load_state(int pn, struct PCB pcb[], int core) {  // restores registers from given process
    PC[core] = pcb[pn].pc;
    ACC[core] = pcb[pn].acc;
    if (pcb[pn].state != 2) {
        pcb[pn].state = 1;
    }
    PN[core] = pcb[pn].pid;
}
// Perform context switches
void contextSwitch(int currentProcess, int nextProcess, struct PCB pcb[], int core) {
    // Save current process state, load next process state
    save_state(currentProcess, pcb, core);
    load_state(nextProcess, pcb, core);
}

// determines what the next process in the queue is [ROUND ROBIN]
int nextP(int pn, struct PCB pcb[], int core) {
    int result = -1;
    for (int i = pn + 1; i < MAX_PROCESSES; i++) {
        if (pcb[i].state != 2) {
            result = i;
        }
    }
    if (result == -1) {
        for (int j = 0; j < pn; j++) {
            if (pcb[j].state != 2) {
                result = j;
            }
        }
    }
    if (result == -1) {
        if (pcb[pn].state == 2) {
            result = pn;
            FF[core] = 1;
        } else {
            result = pn;
        }
    }

    return result;
}

// Dispatcher function
void dispatcher(int currentProcess, int nextProcess, struct PCB pcb[], int core) {
    contextSwitch(currentProcess, nextProcess, pcb, core);  // Perform context switch
}

// Represents a block of memory with a PID, starting address, ending address, and availability flag
struct ProcessMemoryBlock {
    int processID;
    int memoryStart;
    int memoryEnd;
    int isFree;  // 1 = Free, 0 = Allocated
};

// return a memory block
int getMemBlock(int pid, struct ProcessMemoryBlock pmb[]) {
    int result = -1;
    for (int i = 0; i < (MAX_PROCESSES); i++) {
        if (pmb[i].processID == pid) {
            result = i;
        }
    }

    if (result >= 0) {
        return result;
    } else {
        printf("Error: getMemBlock : process %d does not have a block. \n", pid);
        EF[0] = 1;  // update [0] to core tracking
    }
}

// allocate block memory for a PID
void* allocateMemoryBody(int processID, int size, struct ProcessMemoryBlock pmb[]) {
    // Implement First-Fit or Best-Fit allocation strategy
    int best = -1;

    for (int i = 0; i < MAX_PROCESSES+1; i++) {
        printf("allocation attempt for process %d \n", processID);
        if (pmb[i].isFree == 1) {
            // printf("memoryTable[%d] is free! \n", i);
            if (size <= (pmb[i].memoryEnd - pmb[i].memoryStart + 1)) {
                // printf("size is <= block size! \n");
                if (best == -1) {
                    // printf("best found by default! \n");
                    best = i;
                } else if ((pmb[i].memoryEnd - pmb[i].memoryStart + 1) <
                           (pmb[best].memoryEnd - pmb[best].memoryStart + 1)) {
                    // printf("best found by comparison! \n");
                    best = i;
                } else {
                    // printf("best not found. \n");
                }
            } else {
                // printf("size is > block size. \n");
            }
        } else {
            // printf("memoryTable[%d] is not free. \n", i);
        }
    }

    if (best == -1) {
        printf("allocateMemory : processID %d : no memory available...waiting \n", processID);
        EF[0] = 1;
    } else {
        printf("allocateMemory : allocation successful for process %d in block %d \n", processID,
               best);
        pmb[best].isFree = 0;
        pmb[best].processID = processID;
    }
}

// deallocate a block of memory by PID
void* deallocateMemoryBody(int processID, struct ProcessMemoryBlock pmb[]) {
    // Implement logic to free allocated memory
    for (int i = 0; i < MAX_PROCESSES+1; i++) {
        if (pmb[i].processID == processID) {
            pmb[i].processID = -1;
            pmb[i].isFree = 1;
        }
    }
}

// checks if the core is finished or not
void checkFinish(int core, struct PCB pcb[]) {
    int result = 1;
    for (int i = 0; i < MAX_PROCESSES; i++) {
        if (pcb[i].state != 2) {
            result = 0;
        }
    }
    FF[core] = result;
    sleep(1);
}

// return the priority of the given PID
/*int getPri(int wantedPID, struct PCB pcb[]) {
  for (int i = 0; i<sizeof(pcb)/sizeof(pcb[0]); i++){
    if (pcb[i].pid = wantedPID)
      return i;
  }
}*/
// Determine the next process via [Priority Scheduler] (Priority is ascending (5>1))
int nextPPriority(int pn, struct PCB pcb[], int core) {
    int bestPri = -1;
    int bestPID;
    for (int i = 0; i < MAX_PROCESSES; i++) {
        if (pcb[i].pri > bestPri && pcb[i].state != 2) {
            bestPri = pcb[i].pri;
            bestPID = i;
        }
    }
    if (bestPri = -1) {
        FF[core] = 1;
        return pn;
    } else {
        return bestPID;
    }
}

//wrapper function for handling instructions
void* cpuTask(void* arg) {
    int core = *((int*)arg);
    free(arg);
    fetch(core);
    execute(core);
  
    return NULL;
}
// store arguments for each memory task
struct MemoryTaskArgs {
  int msg;
  int pn;
  int size;
  int core;
  struct ProcessMemoryBlock pmb[];
};

//wrapper function for executing memory allocation
void* memoryTask(void* args) {
  pthread_mutex_lock(&memory_mutex);
  
  struct MemoryTaskArgs* threadArgs = (struct MemoryTaskArgs*)args;
  int msg = threadArgs->msg;
  int pn = threadArgs->pn;
  int size = threadArgs->size;
  int core = threadArgs->core;
  struct ProcessMemoryBlock* pmb = threadArgs->pmb;
  
  if (msg == 1) {
    allocateMemoryBody(pn, size, pmb);
  } else if (msg == 2) {
    deallocateMemoryBody(pn, pmb);
  }
  
  pthread_mutex_unlock(&memory_mutex);
}

// Define the argument struct for scheduler
struct SchedulerArgs {
    int core;
    struct ProcessMemoryBlock* pmb;
    struct PCB* pcb;
};
// scheduler header
void scheduler(int core, struct ProcessMemoryBlock pmb[], struct PCB pcb[]);
// Wrapper function for scheduler
void* schedulerTask(void* arg) {
    struct SchedulerArgs* args = (struct SchedulerArgs*)arg;
    scheduler(args->core, args->pmb, args->pcb);
    //free(args); // Free dynamically allocated memory
    return NULL;
}

// Scheduler function; handles executing process and switching between them
void scheduler(int core, struct ProcessMemoryBlock pmb[], struct PCB pcb[]) {
    clock_t startTime = clock();
    current_time = clock();
    while (1) {
        int next;
        pthread_mutex_t cpuMutex;
        
        pthread_t cpuTask_thread;
        int* arg = malloc(sizeof(int));
        *arg = core;
        pthread_mutex_init(&cpuMutex, NULL);
        //printf("\nCreating cputask");
        pthread_create(&cpuTask_thread, NULL, cpuTask, arg);
        //printf("\nJoining cputask");
        pthread_join(cpuTask_thread, NULL);
        pthread_mutex_destroy(&cpuMutex);
        //printf("\ncputask complete");
        ///fetch(core);
        // decode();
        ///execute(core);
        

        clock_t endTime = clock();
        double elapsed_time_ms = (endTime - startTime);

        if (EF[core] == 1) {
            break;
        }

        if (PC[core] >= (pmb[getMemBlock(PN[core], pmb)].memoryEnd -
                         pmb[getMemBlock(PN[core], pmb)].memoryStart + 1)) {
            pcb[PN[core]].state = 2;
        }

        checkFinish(core, pcb);

        if (pcb[PN[core]].state == 2) {
            struct MemoryTaskArgs args;
            args.msg = 2;
            args.pn = PN[core];
            args.size = 0;
            args.core = core;
            args.pmb->isFree = pmb->isFree;
            args.pmb->memoryStart = pmb->memoryStart;
            args.pmb->memoryEnd = pmb->memoryEnd;
            args.pmb->processID = pmb->processID;

            pthread_t memoryTask_thread;
            pthread_create(&memoryTask_thread, NULL, memoryTask, &args);
            pthread_join(memoryTask_thread, NULL);

            deallocateMemoryBody(PN[core], pmb);
            dispatcher(PN[core], nextPPriority(PN[core], pcb, core), pcb, core);

            startTime = clock();
        } else if (elapsed_time_ms >= 3) {
            contextSwitch(PN[core], nextPPriority(PN[core], pcb, core), pcb, core);
            startTime = clock();
        }

        if (FF[core] == 1) {
            printf("Core Complete!!!! \n");
            break;
        }
    }
}

// body for timer interrupt thread
void* timerInterruptBody(void* args) {
    struct InterArgs* threadArgs = (struct InterArgs*)args;

    int core = threadArgs->core;
    struct PCB pcb[MAX_PROCESSES];
    pcb->acc = threadArgs->pcb->acc;
    pcb->pc = threadArgs->pcb->pc;
    pcb->pid = threadArgs->pcb->pid;
    pcb->pri = threadArgs->pcb->pri;
    pcb->state = threadArgs->pcb->state;

    printf("Handling Timer Interrupt\n");
    dispatcher(PN[core], nextPPriority(PN[core], pcb, core), pcb, core);
}

// timer interrupt in a thread
void timerInterrupt(int core, struct PCB pcb[]) {
    struct InterArgs args;
    args.core = core;
    args.pcb->acc = pcb->acc;
    args.pcb->pc = pcb->pc;
    args.pcb->pri = pcb->pri;
    args.pcb->pid = pcb->pid;
    args.pcb->state = pcb->state;
    pthread_t thread;
    pthread_create(&thread, NULL, timerInterruptBody, &args);
    pthread_join(thread, NULL);
}
// body for io interrupt thread
void* ioInterruptBody(void* args) {
    struct InterArgs* threadArgs = (struct InterArgs*)args;

    int core = threadArgs->core;
    struct PCB pcb[MAX_PROCESSES];
    pcb->acc = threadArgs->pcb->acc;
    pcb->pc = threadArgs->pcb->pc;
    pcb->pid = threadArgs->pcb->pid;
    pcb->pri = threadArgs->pcb->pri;
    pcb->state = threadArgs->pcb->state;

    printf("Handling IO Interrupt\n");
    dispatcher(PN[core], nextPPriority(PN[core], pcb, core), pcb, core);
}

// io interrupt in a thread
void ioInterrupt(int core, struct PCB pcb[]) {
    struct InterArgs args;
    args.core = core;
    args.pcb->acc = pcb->acc;
    args.pcb->pc = pcb->pc;
    args.pcb->pri = pcb->pri;
    args.pcb->pid = pcb->pid;
    args.pcb->state = pcb->state;
    pthread_t thread;
    pthread_create(&thread, NULL, ioInterruptBody, &args);
    pthread_join(thread, NULL);
}
// system call interrupt body
void* sysCallInterruptBody(void* args) {
    struct InterArgs* threadArgs = (struct InterArgs*)args;

    int core = threadArgs->core;
    struct PCB pcb[MAX_PROCESSES];
    pcb->acc = threadArgs->pcb->acc;
    pcb->pc = threadArgs->pcb->pc;
    pcb->pid = threadArgs->pcb->pid;
    pcb->pri = threadArgs->pcb->pri;
    pcb->state = threadArgs->pcb->state;

    printf("Handling System Call Interrupt\n");
    dispatcher(PN[core], nextPPriority(PN[core], pcb, core), pcb, core);
}

// timer interrupt in a thread
void sysCallInterrupt(int core, struct PCB pcb[]) {
    struct InterArgs args;
    args.core = core;
    args.pcb->acc = pcb->acc;
    args.pcb->pc = pcb->pc;
    args.pcb->pri = pcb->pri;
    args.pcb->pid = pcb->pid;
    args.pcb->state = pcb->state;
    pthread_t thread;
    pthread_create(&thread, NULL, sysCallInterruptBody, &args);
    pthread_join(thread, NULL);
}
// trap interrupts body
void* trapInterruptBody(void* args) {
    struct InterArgs* threadArgs = (struct InterArgs*)args;

    int core = threadArgs->core;
    struct PCB pcb[MAX_PROCESSES];
    pcb->acc = threadArgs->pcb->acc;
    pcb->pc = threadArgs->pcb->pc;
    pcb->pid = threadArgs->pcb->pid;
    pcb->pri = threadArgs->pcb->pri;
    pcb->state = threadArgs->pcb->state;

    printf("Handling Trap Interrupt\n");
    dispatcher(PN[core], nextPPriority(PN[core], pcb, core), pcb, core);
}

// timer interrupt in a thread
void trapInterrupt(int core, struct PCB pcb[]) {
    struct InterArgs args;
    args.core = core;
    args.pcb->acc = pcb->acc;
    args.pcb->pc = pcb->pc;
    args.pcb->pri = pcb->pri;
    args.pcb->pid = pcb->pid;
    args.pcb->state = pcb->state;
    pthread_t thread;
    pthread_create(&thread, NULL, trapInterruptBody, &args);
    pthread_join(thread, NULL);
}

// Function to simulate the instruction cycle with concurrency
void* cpuCore(void* arg) {
    int core = *((int*)arg);
    //free(arg);  // Free allocated memory for the core ID

    struct PCB processTable[MAX_PROCESSES];

    // Initialize the processes
    for (int i = 0; i < MAX_PROCESSES; i++) {
        processTable[i].pid = i;
        processTable[i].pc = 0;
        processTable[i].acc = 0;
        processTable[i].state = 0;  // Ready state
    }

    // initialize process memory table
    struct ProcessMemoryBlock processMemoryTable[4];  // Example: divide RAM into blocks

    int c = 0;  // current block size
    int j = 0;  // current RAM address
    for (int i = 0; i < 4; i++) {
        processMemoryTable[i].processID = -1;  // Mark all blocks as free
        processMemoryTable[i].isFree = 1;

        if (((c + 20) >= (RAM_SIZE / (NUM_CORES + 1))) || (i == (4 - 1))) {
            processMemoryTable[i].memoryStart = j + coreMemoryTable[core].memoryStart;
            processMemoryTable[i].memoryEnd = (coreMemoryTable[core].memoryEnd);
        } else {
            processMemoryTable[i].memoryStart = j + coreMemoryTable[core].memoryStart;
            c += 20;
            processMemoryTable[i].memoryEnd = ((j + c) - 1) + coreMemoryTable[core].memoryStart;
            j = j + c;
        }
        printf("Size of block %d = %d \n", i,
               (processMemoryTable[i].memoryEnd - processMemoryTable[i].memoryStart + 1));
    }
    ////////////////////////////
    allocateMemoryBody(0, 10, processMemoryTable);
    allocateMemoryBody(1, 10, processMemoryTable);
    allocateMemoryBody(2, 10, processMemoryTable);
    
    
    
    
    
    
    struct SchedulerArgs args1 = {core, processMemoryTable, processTable};
    pthread_t schedulingTask_thread;
    schedulerstart=clock();
    pthread_create(&schedulingTask_thread, NULL, schedulerTask, &args1);
    pthread_join(schedulingTask_thread, NULL);
    schedulerend=clock();
    //scheduler(core, processMemoryTable, processTable);
    return NULL;
}


// make and handle random interrupts
void* generateInterrupts(void* arg) {
    struct PCB testErrorPCB = {0,0,0,0,0};
    while (1) {
        sleep(1);                                     // delay to simulate interrupt timing
        int interruptType = rand() % MAX_INTERRUPTS;  // dandomly select an interrupt type
        switch(interruptType)   {             // handle the generated interrupt
          case 0:
            timerInterrupt(0,&testErrorPCB);
            break;
          case 1:
            ioInterrupt(0,&testErrorPCB);
            break;
          case 2:
            sysCallInterrupt(0,&testErrorPCB);
            break;
          case 3:
            trapInterrupt(0,&testErrorPCB);
            break;
        }
    }
    return NULL;
}

//lock for buffer operations
pthread_mutex_t buffer_mutex;
sem_t buffer_full, buffer_empty;

//the buffer
int buffer[BUFFER_SIZE];
int buffer_index = 0;

int counter = 2345;

//writes data into the buffer
void* producer(void* arg) {
		sem_wait(&buffer_empty);
		pthread_mutex_lock(&buffer_mutex);

		buffer[buffer_index] = counter;
		counter += 1;
		printf("Produced data: %d \n", buffer[buffer_index]);
		buffer_index = (buffer_index + 1) % BUFFER_SIZE;

		pthread_mutex_unlock(&buffer_mutex);
		sem_post(&buffer_full);

	return NULL;
}

//extracts data from the buffer
void* consumer(void* arg) {

		sem_wait(&buffer_full);
		pthread_mutex_lock(&buffer_mutex);

		int data = buffer[(buffer_index - 1 + BUFFER_SIZE) % BUFFER_SIZE];
		printf("Consumed data: %d \n", data);

		pthread_mutex_unlock(&buffer_mutex);
		sem_post(&buffer_empty);

	return NULL;
}




// determine the next process using priority
int nextPPri(time_t start, int pn, struct PCB pcb[], int core) {
    time_t curr = time(NULL);
    int result = -1;
    for (int i = 0; i < MAX_PROCESSES; i++) {
        if ((pcb[i].state != 2) && (result == -1) && ((curr - start) > pcb[i].arrivalTime)) {
            result = i;
        } else if ((pcb[i].state != 2) && (pcb[i].pri > pcb[result].pri) && ((curr - start) > pcb[i].arrivalTime)) {
            result = i;
        }
    }
   int allArrived = 1;
    for (int i = 0; i < MAX_PROCESSES; i++) {
        if ((pcb[i].state != 2) && ((curr - start) < pcb[i].arrivalTime)) {
            allArrived = 0;
        }
    }
    if (result == -1) {
        if (allArrived == 0) {
            printf("Waiting for process to arrive... \n");
            sleep(1);
            return nextPPri(start, pn, pcb, core);
        } else if (pcb[pn].state == 2) {
            result = pn;
            FF[core] = 1;
        } else {
            result = pn;
        }
    }
    printf("next process is %d \n", result);
    return result;
}
// schedule processes using priorities
void priorityScheduler(int core, struct ProcessMemoryBlock pmb[], struct PCB pcb[]) {
    time_t core_start = time(NULL);
    time_t slice_start = time(NULL);
    time_t curr = time(NULL);

    contextSwitch(PN[core], nextPPri(core_start, PN[core], pcb, core), pcb, core);
    slice_start = time(NULL);

    while(1) {

        fetch(core);
        execute(core);
        sleep(1);

        if (PC[core] >= (pmb[getMemBlock(PN[core], pmb)].memoryEnd - pmb[getMemBlock(PN[core], pmb)].memoryStart + 1)) {
            pcb[PN[core]].state = 2;
        }

        curr = time(NULL);
        time_t elapsed = curr - slice_start;
        pcb[PN[core]].timeremaining -= (int)(elapsed);

        

        if (pcb[PN[core]].timeremaining <= 0) {
            pcb[PN[core]].state = 2;
        }

        for (int i = 0; i < MAX_PROCESSES; i++) {
            if (pcb[i].state != 2) {
                int waitTime = (int) (curr - (core_start + pcb[i].arrivalTime));
                waitTable[i]=waitTime;
                burstTable[i]=pcb[i].burstTime;
                int response_ratio = (int) ((waitTime + pcb[i].burstTime) / pcb[i].burstTime);
                pcb[i].responseRatio = response_ratio;
            }
        }


	//printf("Start of slice: %ld \n", slice_start);
	//printf("Current time: %ld \n", curr);
	printf("Time elapsed: %ld \n", elapsed);

        if (pcb[PN[core]].state == 2) {
            contextSwitch(PN[core], nextPPri(core_start, PN[core], pcb, core), pcb, core);
            slice_start = time(NULL);
        } else if (TIME_QUANTUM <= elapsed) {
            contextSwitch(PN[core], nextPPri(core_start, PN[core], pcb, core), pcb, core);
            slice_start = time(NULL);
        }

        checkFinish(core, pcb);

        if (FF[core] == 1) {
            printf("Core %d complete!!! \n", core);
            break;
        }



    }
}

// select the next process using the SRT algorithm
int nextPSRT(time_t start, int pn, struct PCB pcb[], int core) {
    time_t curr = time(NULL);
    int result = -1;
    for (int i = 0; i < MAX_PROCESSES; i++) {
        if ((pcb[i].state != 2) && (result == -1) && ((curr - start) > pcb[i].arrivalTime)) {
            result = i;
        } else if ((pcb[i].state != 2) && (pcb[i].timeremaining < pcb[result].timeremaining) && ((curr - start) > pcb[i].arrivalTime)) {
            result = i;
        }
    }

    int allArrived = 1;
    for (int i = 0; i < MAX_PROCESSES; i++) {
        if ((pcb[i].state != 2) && ((curr - start) < pcb[i].arrivalTime)) {
            allArrived = 0;
        }
    }
    if (result == -1) {
        if (allArrived == 0) {
            printf("Waiting for process to arrive... \n");
            sleep(1);
            return nextPSRT(start, pn, pcb, core);
        } else if (pcb[pn].state == 2) {
            result = pn;
            FF[core] = 1;
        } else {
            result = pn;
        }
    }
    printf("next process is %d \n", result);
    return result;
}

// shecdule proccesses using SRT
void SRTScheduler(int core, struct ProcessMemoryBlock pmb[], struct PCB pcb[]) {
    time_t core_start = time(NULL);
    time_t slice_start = time(NULL);
    time_t curr = time(NULL);

    contextSwitch(PN[core], nextPSRT(core_start, PN[core], pcb, core), pcb, core);
    slice_start = time(NULL);

    while(1) {

        
        fetch(core);
        execute(core);
        sleep(1);

        if (PC[core] >= (pmb[getMemBlock(PN[core], pmb)].memoryEnd - pmb[getMemBlock(PN[core], pmb)].memoryStart + 1)) {
            pcb[PN[core]].state = 2;
        }

        curr = time(NULL);
        time_t elapsed = curr - slice_start;
        pcb[PN[core]].timeremaining -= (int)(elapsed);

        

        if (pcb[PN[core]].timeremaining <= 0) {
            pcb[PN[core]].state = 2;
        }

        for (int i = 0; i < MAX_PROCESSES; i++) {
            if (pcb[i].state != 2) {
                int waitTime = (int) (curr - (core_start + pcb[i].arrivalTime));
                waitTable[i]=waitTime;
                burstTable[i]=pcb[i].burstTime;
                int response_ratio = (int) ((waitTime + pcb[i].burstTime) / pcb[i].burstTime);
                pcb[i].responseRatio = response_ratio;
            }
        }



	//printf("Start of slice: %ld \n", slice_start);
	//printf("Current time: %ld \n", curr);
	printf("Time elapsed: %ld \n", elapsed);

        if (pcb[PN[core]].state == 2) {
            contextSwitch(PN[core], nextPSRT(core_start, PN[core], pcb, core), pcb, core);
            slice_start = time(NULL);
        } else if (TIME_QUANTUM <= elapsed) {
            contextSwitch(PN[core], nextPSRT(core_start, PN[core], pcb, core), pcb, core);
            slice_start = time(NULL);
        }

        checkFinish(core, pcb);

        if (FF[core] == 1) {
            printf("Core %d complete!!! \n", core);
            break;
        }



    }
}
// select the next process using HRRN
int nextPHRRN(time_t start, int pn, struct PCB pcb[], int core) {
    int result = -1;
    time_t curr = time(NULL);
    for (int i = 0; i < MAX_PROCESSES; i++) {
        if ((pcb[i].state != 2) && (result == -1) && ((curr - start) > pcb[i].arrivalTime)) {
            result = i;
        } else if ((pcb[i].state != 2) && (pcb[i].responseRatio > pcb[result].responseRatio) && ((curr - start) > pcb[i].arrivalTime)) {
            result = i;
        }
    }
    int allArrived = 1;
    for (int i = 0; i < MAX_PROCESSES; i++) {
        if ((pcb[i].state != 2) && ((curr - start) < pcb[i].arrivalTime)) {
            allArrived = 0;
        }
    }
    if (result == -1) {
        if (allArrived == 0) {
            printf("Waiting for process to arrive... \n");
            sleep(1);
            return nextPHRRN(start, pn, pcb, core);
        } else if (pcb[pn].state == 2) {
            result = pn;
            FF[core] = 1;
        } else {
            result = pn;
        }
    }
    printf("next process is %d \n", result);
    return result;
}
// schedule processes using HRRN
void HRRNScheduler(int core, struct ProcessMemoryBlock pmb[], struct PCB pcb[]) {
    time_t core_start = time(NULL);
    time_t slice_start = time(NULL);
    time_t curr = time(NULL);

    contextSwitch(PN[core], nextPHRRN(core_start, PN[core], pcb, core), pcb, core);
    slice_start = time(NULL);

    while(1) {

        
        fetch(core);
        execute(core);
        sleep(1);

        if (PC[core] >= (pmb[getMemBlock(PN[core], pmb)].memoryEnd - pmb[getMemBlock(PN[core], pmb)].memoryStart + 1)) {
            pcb[PN[core]].state = 2;
        }

        curr = time(NULL);
        time_t elapsed = curr - slice_start;
        pcb[PN[core]].timeremaining -= (int)(elapsed);

        

        if (pcb[PN[core]].timeremaining <= 0) {
            pcb[PN[core]].state = 2;
        }

        for (int i = 0; i < MAX_PROCESSES; i++) {
            if (pcb[i].state != 2) {
                int waitTime = (int) (curr - (core_start + pcb[i].arrivalTime));
                waitTable[i]=waitTime;
                burstTable[i]=pcb[i].burstTime;
                int response_ratio = (int) ((waitTime + pcb[i].burstTime) / pcb[i].burstTime);
                pcb[i].responseRatio = response_ratio;
            }
        }


	//printf("Start of slice: %ld \n", slice_start);
	//printf("Current time: %ld \n", curr);
	printf("Time elapsed: %ld \n", elapsed);

        if (pcb[PN[core]].state == 2) {
            contextSwitch(PN[core], nextPHRRN(core_start, PN[core], pcb, core), pcb, core);
            slice_start = time(NULL);
        //} else if (TIME_QUANTUM <= elapsed) {
        //    contextSwitch(PN[core], nextPHRRN(PN[core], pcb, core), pcb, core);
        //    slice_start = time(NULL);
        }

        checkFinish(core, pcb);

        if (FF[core] == 1) {
            printf("Core %d complete!!! \n", core);
            break;
        }



    }
}
// select next proccess using Round Robin
int nextPRR(time_t start, int pn, struct PCB pcb[], int core) {
    int result = -1;
    time_t curr = time(NULL);
    for (int i = pn + 1; i < MAX_PROCESSES; i++) {
        if ((pcb[i].state != 2) && ((curr - start) > pcb[i].arrivalTime)) {
            result = i;
        }
    }
    if (result == -1) {
        for (int j = 0; j < pn; j++) {
            if ((pcb[j].state != 2) && ((curr - start) > pcb[j].arrivalTime)) {
                result = j;
            }
        }
    }
    if (result == -1) {
        if ((pcb[pn].state != 2) && ((curr - start) > pcb[pn].arrivalTime)) {
            result = pn;
        }
    }
    int allArrived = 1;
    for (int i = 0; i < MAX_PROCESSES; i++) {
        if ((pcb[i].state != 2) && ((curr - start) < pcb[i].arrivalTime)) {
            allArrived = 0;
        }
    }
    if (result == -1) {
        if (allArrived == 0) {
            printf("Waiting for process to arrive... \n");
            sleep(1);
            return nextPRR(start, pn, pcb, core);
        } else if (pcb[pn].state == 2) {
            result = pn;
            FF[core] = 1;
        } else {
            result = pn;
        }
    }
    printf("next process is %d \n", result);
    return result;
}
// schedule processes using round robin
void RRScheduler(int core, struct ProcessMemoryBlock pmb[], struct PCB pcb[]) {
    time_t core_start = time(NULL);
    time_t slice_start = time(NULL);
    time_t curr = time(NULL);

    contextSwitch(PN[core], nextPRR(core_start, PN[core], pcb, core), pcb, core);
    slice_start = time(NULL);

    while(1) {

        
        fetch(core);
        execute(core);
        sleep(1);

        if (PC[core] >= (pmb[getMemBlock(PN[core], pmb)].memoryEnd - pmb[getMemBlock(PN[core], pmb)].memoryStart + 1)) {
            pcb[PN[core]].state = 2;
             turnaroundTable[PC[core]] = pcb[PN[core]].arrivalTime+waitTable[PN[core]]; //arrival time in unix
        }

        curr = time(NULL);
        time_t elapsed = curr - slice_start;
        pcb[PN[core]].timeremaining -= (int)(elapsed);

        

        if (pcb[PN[core]].timeremaining <= 0) {
            pcb[PN[core]].state = 2;
        }

        for (int i = 0; i < MAX_PROCESSES; i++) {
            if (pcb[i].state != 2) {
                int waitTime = (int) (curr - (core_start + pcb[i].arrivalTime));
                waitTable[i]=waitTime;
                burstTable[i]=pcb[i].burstTime;
                int response_ratio = (int) ((waitTime + pcb[i].burstTime) / pcb[i].burstTime);
                pcb[i].responseRatio = response_ratio;
            }
        }


	//printf("Start of slice: %ld \n", slice_start);
	//printf("Current time: %ld \n", curr);
	printf("Time elapsed: %ld \n", elapsed);

        if (pcb[PN[core]].state == 2) {
            contextSwitch(PN[core], nextPRR(core_start, PN[core], pcb, core), pcb, core);
            slice_start = time(NULL);
        } else if (TIME_QUANTUM <= elapsed) {
            contextSwitch(PN[core], nextPRR(core_start, PN[core], pcb, core), pcb, core);
            slice_start = time(NULL);
        }

        checkFinish(core, pcb);

        if (FF[core] == 1) {
            printf("Core %d complete!!! \n", core);
            break;
        }



    }
}
// select next processes using FCFS
int nextPFCFS(time_t start, int pn, struct PCB pcb[], int core) {
    int result = -1;
    time_t curr = time(NULL);
    for (int i = 0; i < MAX_PROCESSES; i++) {
        if ((pcb[i].state != 2) && (result == -1) && ((curr - start) > pcb[i].arrivalTime)) {
            result = i;
        } else if ((pcb[i].state != 2) && (pcb[i].arrivalTime < pcb[result].arrivalTime) && ((curr - start) > pcb[i].arrivalTime)) {
            result = i;
        }
    }
    int allArrived = 1;
    for (int i = 0; i < MAX_PROCESSES; i++) {
        if ((pcb[i].state != 2) && ((curr - start) < pcb[i].arrivalTime)) {
            allArrived = 0;
        }
    }
    if (result == -1) {
        if (allArrived == 0) {
            printf("Waiting for process to arrive... \n");
            sleep(1);
            return nextPFCFS(start, pn, pcb, core);
        } else if (pcb[pn].state == 2) {
            result = pn;
            FF[core] = 1;
        } else {
            result = pn;
        }
    }
    printf("next process is %d \n", result);
    return result;
}
// schedule processes using FCFS
void FCFSScheduler(int core, struct ProcessMemoryBlock pmb[], struct PCB pcb[]) {
    time_t core_start = time(NULL);
    time_t slice_start = time(NULL);
    time_t curr = time(NULL);

    contextSwitch(PN[core], nextPHRRN(core_start, PN[core], pcb, core), pcb, core);
    slice_start = time(NULL);

    while(1) {

        
        fetch(core);
        execute(core);
        sleep(1);

        if (PC[core] >= (pmb[getMemBlock(PN[core], pmb)].memoryEnd - pmb[getMemBlock(PN[core], pmb)].memoryStart + 1)) {
            pcb[PN[core]].state = 2;
        }

        curr = time(NULL);
        time_t elapsed = curr - slice_start;
        pcb[PN[core]].timeremaining -= (int)(elapsed);

        

        if (pcb[PN[core]].timeremaining <= 0) {
            pcb[PN[core]].state = 2;
        }

        for (int i = 0; i < MAX_PROCESSES; i++) {
            if (pcb[i].state != 2) {
                int waitTime = (int) (curr - (core_start + pcb[i].arrivalTime));
                waitTable[i]=waitTime;
                burstTable[i]=pcb[i].burstTime;
                int response_ratio = (int) ((waitTime + pcb[i].burstTime) / pcb[i].burstTime);
                pcb[i].responseRatio = response_ratio;
            }
        }


	//printf("Start of slice: %ld \n", slice_start);
	//printf("Current time: %ld \n", curr);
	printf("Time elapsed: %ld \n", elapsed);

        if (pcb[PN[core]].state == 2) {
            contextSwitch(PN[core], nextPFCFS(core_start, PN[core], pcb, core), pcb, core);
            slice_start = time(NULL);
        //} else if (TIME_QUANTUM <= elapsed) {
        //    contextSwitch(PN[core], nextPHRRN(PN[core], pcb, core), pcb, core);
        //    slice_start = time(NULL);
        }

        checkFinish(core, pcb);

        if (FF[core] == 1) {
            printf("Core %d complete!!! \n", core);
            break;
        }



    }
}
// select next processes using SPN
int nextPSPN(time_t start, int pn, struct PCB pcb[], int core) {
    int result = -1;
    time_t curr = time(NULL);
    for (int i = 0; i < MAX_PROCESSES; i++) {
        if ((pcb[i].state != 2) && (result == -1) && ((curr - start) > pcb[i].arrivalTime)) {
            result = i;
        } else if ((pcb[i].state != 2) && (pcb[i].burstTime < pcb[result].burstTime) && ((curr - start) > pcb[i].arrivalTime)) {
            result = i;
        }
    }
    int allArrived = 1;
    for (int i = 0; i < MAX_PROCESSES; i++) {
        if ((pcb[i].state != 2) && ((curr - start) < pcb[i].arrivalTime)) {
            allArrived = 0;
        }
    }
    if (result == -1) {
        if (allArrived == 0) {
            printf("Waiting for process to arrive... \n");
            sleep(1);
            return nextPSPN(start, pn, pcb, core);
        } else if (pcb[pn].state == 2) {
            result = pn;
            FF[core] = 1;
        } else {
            result = pn;
        }
    }
    printf("next process is %d \n", result);
    return result;
}
// schedule processes using SPN
void SPNScheduler(int core, struct ProcessMemoryBlock pmb[], struct PCB pcb[]) {
    time_t core_start = time(NULL);
    time_t slice_start = time(NULL);
    time_t curr = time(NULL);

    contextSwitch(PN[core], nextPHRRN(core_start, PN[core], pcb, core), pcb, core);
    slice_start = time(NULL);

    while(1) {

        
        fetch(core);
        execute(core);
        sleep(1);

        if (PC[core] >= (pmb[getMemBlock(PN[core], pmb)].memoryEnd - pmb[getMemBlock(PN[core], pmb)].memoryStart + 1)) {
            pcb[PN[core]].state = 2;
        }

        curr = time(NULL);
        time_t elapsed = curr - slice_start;
        pcb[PN[core]].timeremaining -= (int)(elapsed);

        

        if (pcb[PN[core]].timeremaining <= 0) {
            pcb[PN[core]].state = 2;
        }

        for (int i = 0; i < MAX_PROCESSES; i++) {
            if (pcb[i].state != 2) {
                int waitTime = (int) (curr - (core_start + pcb[i].arrivalTime));
                waitTable[i]=waitTime;
                burstTable[i]=pcb[i].burstTime;
                int response_ratio = (int) ((waitTime + pcb[i].burstTime) / pcb[i].burstTime);
                pcb[i].responseRatio = response_ratio;
            }
        }


	//printf("Start of slice: %ld \n", slice_start);
	//printf("Current time: %ld \n", curr);
	printf("Time elapsed: %ld \n", elapsed);

        if (pcb[PN[core]].state == 2) {
            contextSwitch(PN[core], nextPSPN(core_start, PN[core], pcb, core), pcb, core);
            slice_start = time(NULL);
        //} else if (TIME_QUANTUM <= elapsed) {
        //    contextSwitch(PN[core], nextPHRRN(PN[core], pcb, core), pcb, core);
        //    slice_start = time(NULL);
        }

        checkFinish(core, pcb);

        if (FF[core] == 1) {
            printf("Core %d complete!!! \n", core);
            break;
        }



    }
}
// schedule and select next processes using feedBack with FCFS queues
void feedBackScheduler(int core, struct ProcessMemoryBlock pmb[], struct PCB pcb[]) {
    int TIME_QUANTUM1 = 3;
    int TIME_QUANTUM2 = 6;
    time_t core_start = time(NULL);
    time_t slice_start = time(NULL);
    time_t curr = time(NULL);

    int q1[MAX_PROCESSES];
    int q2[MAX_PROCESSES];
    int q3[MAX_PROCESSES];

    for (int i = 0; i < MAX_PROCESSES; i++) {
        q1[i] = -1;
        q2[i] = -1;
        q3[i] = -1;
    }

    while (1) {
        curr = time(NULL);
        //put new processes in q1
        for (int i = 0; i < MAX_PROCESSES; i++) {
            if ((pcb[i].state != 2) && ((curr - core_start) < pcb[i].arrivalTime)) {
                if ((q1[i] == -1) && (q2[i] == -1) && (q3[i] == -1)) {
                    q1[i] = i;
                }
            }
        }

        int empty1 = 1;
        for (int i = 0; i < MAX_PROCESSES; i++) {
            if (q1[i] != -1) {
                empty1 = 0;
            }
        }
        int empty2 = 1;
        for (int i = 0; i < MAX_PROCESSES; i++) {
            if (q2[i] != -1) {
                empty2 = 0;
            }
        }
        int empty3 = 1;
        for (int i = 0; i < MAX_PROCESSES; i++) {
            if (q3[i] != -1) {
                empty3 = 0;
            }
        }
        if (empty1 == 0) {
            printf("In queue 1 \n");
            for (int i = 0; i < MAX_PROCESSES; i++) {
                if (q1[i] != -1) {
                   
                    contextSwitch(PN[core], i, pcb, core);
                    printf("next process is %d \n", i);

                    while (1) {
                        fetch(core);
                        execute(core);
                        sleep(1);

                        if (PC[core] >= (pmb[getMemBlock(PN[core], pmb)].memoryEnd - pmb[getMemBlock(PN[core], pmb)].memoryStart + 1)) {
                            pcb[PN[core]].state = 2;
                        }

                        curr = time(NULL);
                        time_t elapsed = curr - slice_start;
                        pcb[PN[core]].timeremaining -= (int)(elapsed);

                        if (pcb[PN[core]].timeremaining <= 0) {
                            pcb[PN[core]].state = 2;
                        }

                        for (int j = 0; j < MAX_PROCESSES; j++) {
                            if (pcb[j].state != 2) {
                                int waitTime = (int) (curr - (core_start + pcb[j].arrivalTime));
                                waitTable[j]=waitTime;
                                burstTable[j]=pcb[j].burstTime;
                                int response_ratio = (int) ((waitTime + pcb[j].burstTime) / pcb[j].burstTime);
                                pcb[j].responseRatio = response_ratio;
                            }
                        }

                        if (pcb[PN[core]].state == 2) {
                            slice_start = time(NULL);
                            q1[i] = -1;
                            break;
                        } else if (TIME_QUANTUM1 <= elapsed) {
                            q2[i] = i;
                            slice_start = time(NULL);
                            q1[i] = -1;
                            break;
                        }

                    }

                }
            }
            checkFinish(core, pcb);

            if (FF[core] == 1) {
                printf("Core %d complete!!! \n", core);
                break;
            }
        } else if (empty2 == 0) {
            printf("In queue 2 \n");
            for (int i = 0; i < MAX_PROCESSES; i++) {
                if (q2[i] != -1) {
                   
                    contextSwitch(PN[core], q2[i], pcb, core);
                    printf("next process is %d \n", i);

                    while (1) {
                        fetch(core);
                        execute(core);
                        sleep(1);

                        if (PC[core] >= (pmb[getMemBlock(PN[core], pmb)].memoryEnd - pmb[getMemBlock(PN[core], pmb)].memoryStart + 1)) {
                            pcb[PN[core]].state = 2;
                        }

                        curr = time(NULL);
                        time_t elapsed = curr - slice_start;
                        pcb[PN[core]].timeremaining -= (int)(elapsed);

                        if (pcb[PN[core]].timeremaining <= 0) {
                            pcb[PN[core]].state = 2;
                        }

                        for (int j = 0; j < MAX_PROCESSES; j++) {
                            if (pcb[j].state != 2) {
                                int waitTime = (int) (curr - (core_start + pcb[j].arrivalTime));
                                waitTable[j]=waitTime;
                                burstTable[j]=pcb[j].burstTime;
                                int response_ratio = (int) ((waitTime + pcb[j].burstTime) / pcb[j].burstTime);
                                pcb[j].responseRatio = response_ratio;
                            }
                        }

                        if (pcb[PN[core]].state == 2) {
                            slice_start = time(NULL);
                            q2[i] = -1;
                            break;
                        } else if (TIME_QUANTUM2 <= elapsed) {
                            q3[i] = i;
                            slice_start = time(NULL);
                            q2[i] = -1;
                            break;
                        }

                    }

                }
            }
            checkFinish(core, pcb);

            if (FF[core] == 1) {
                printf("Core %d complete!!! \n", core);
                break;
            }
        } else if (empty3 == 0) {
            printf("In queue 3 \n");
            for (int i = 0; i < MAX_PROCESSES; i++) {
                if (q2[i] != -1) {
                   
                    contextSwitch(PN[core], i, pcb, core);
                    printf("next process is %d \n", i);

                    while (1) {
                        fetch(core);
                        execute(core);
                        sleep(1);

                        if (PC[core] >= (pmb[getMemBlock(PN[core], pmb)].memoryEnd - pmb[getMemBlock(PN[core], pmb)].memoryStart + 1)) {
                            pcb[PN[core]].state = 2;
                        }

                        curr = time(NULL);
                        time_t elapsed = curr - slice_start;
                        pcb[PN[core]].timeremaining -= (int)(elapsed);

                        if (pcb[PN[core]].timeremaining <= 0) {
                            pcb[PN[core]].state = 2;
                        }

                        for (int j = 0; j < MAX_PROCESSES; j++) {
                            if (pcb[j].state != 2) {
                                int waitTime = (int) (curr - (core_start + pcb[j].arrivalTime));
                                waitTable[j]=waitTime;
                                 burstTable[j]=pcb[j].burstTime;
                                int response_ratio = (int) ((waitTime + pcb[j].burstTime) / pcb[j].burstTime);
                                pcb[j].responseRatio = response_ratio;
                            }
                        }

                        if (pcb[PN[core]].state == 2) {
                            slice_start = time(NULL);
                            q2[i] = -1;
                            break;
                        //} else if (TIME_QUANTUM2 <= elapsed) {
                        //    q3[i] = i;
                        //    slice_start = time(NULL);
                        //    q2[i] = NULL;
                        //    break;
                        }

                    }

                }
            }
            checkFinish(core, pcb);

            if (FF[core] == 1) {
                printf("Core %d complete!!! \n", core);
                break;
            }
        } else {
            break;
        }

        checkFinish(core, pcb);
        if (FF[core] == 1) {
            printf("Core %d complete!!! \n", core);
            break;
        }
    }


}
// handle initializing processes and selecting scheduling algorithms
void cpuCore4(int schedulingalgorithm) {
    int core = 0;
    //free(arg);  // Free allocated memory for the core ID

    struct PCB processTable[MAX_PROCESSES];

    // Initialize the processes
    for (int i = 0; i < MAX_PROCESSES; i++) {
        processTable[i].pid = i;
        processTable[i].pc = 0;
        processTable[i].acc = 0;
        processTable[i].state = 0;
        processTable[i].pri = 0;
        processTable[i].timeremaining = 0;
        processTable[i].arrivalTime = 0;  // Ready state
    }

    processTable[0].pri = 3;
    processTable[1].pri = 4;
    processTable[2].pri = 2;
    processTable[3].pri = 4;
    processTable[4].pri = 1;
    processTable[5].pri = 8;
    processTable[0].timeremaining = 14;
    processTable[1].timeremaining = 15;
    processTable[2].timeremaining = 16;
    processTable[3].timeremaining = 17;
    processTable[4].timeremaining = 18;
    processTable[5].timeremaining = 19;
    processTable[0].burstTime = 14;
    processTable[1].burstTime = 15;
    processTable[2].burstTime = 16;
    processTable[3].burstTime = 17;
    processTable[4].burstTime = 18;
    processTable[5].burstTime = 19;
    processTable[0].arrivalTime = 5;
    processTable[1].arrivalTime = 4;
    processTable[2].arrivalTime = 3;
    processTable[3].arrivalTime = 2;
    processTable[4].arrivalTime = 1;
    processTable[5].arrivalTime = 0;

    // initialize process memory table
    struct ProcessMemoryBlock processMemoryTable[MAX_PROCESSES+1];  // Example: divide RAM into blocks

    int c = 0;  // current block size
    int j = 0;  // current RAM address
    for (int i = 0; i < MAX_PROCESSES+1; i++) {
        processMemoryTable[i].processID = -1;  // Mark all blocks as free
        processMemoryTable[i].isFree = 1;

        if (((c + 20) >= (RAM_SIZE / (NUM_CORES + 1))) || (i == (MAX_PROCESSES+1 - 1))) {
            processMemoryTable[i].memoryStart = j + coreMemoryTable[core].memoryStart;
            processMemoryTable[i].memoryEnd = (coreMemoryTable[core].memoryEnd);
        } else {
            processMemoryTable[i].memoryStart = j + coreMemoryTable[core].memoryStart;
            c += 20;
            processMemoryTable[i].memoryEnd = ((j + c) - 1) + coreMemoryTable[core].memoryStart;
            j = j + c;
        }
        printf("Size of block %d = %d \n", i,
               (processMemoryTable[i].memoryEnd - processMemoryTable[i].memoryStart + 1));
    }
    ////////////////////////////
    allocateMemoryBody(0, 10, processMemoryTable);
    allocateMemoryBody(1, 10, processMemoryTable);
    allocateMemoryBody(2, 10, processMemoryTable);
    allocateMemoryBody(3, 10, processMemoryTable);
    allocateMemoryBody(4, 10, processMemoryTable);
    allocateMemoryBody(5, 10, processMemoryTable);
    
    //RRScheduler(core, processMemoryTable, processTable);
    //FCFSScheduler(core, processMemoryTable, processTable);
    //priorityScheduler(core, processMemoryTable, processTable);
    //SRTScheduler(core, processMemoryTable, processTable);
    //HRRNScheduler(core, processMemoryTable, processTable);
    //SPNScheduler(core, processMemoryTable, processTable);
    
    switch(schedulingalgorithm) {
        case 0:
            printf("\nRound robin started!");
            RRScheduler(core, processMemoryTable, processTable);
            printf("\nRound Robin complete!");
            printf("\n------Round Robin Q=%d OUTPUT------\n", TIME_QUANTUM);
            printf("\t PID \t WAIT TIME \t BURST TIME \t TURNAROUND TIME\n");
            for (int i=0; i<MAX_PROCESSES; i++){
                printf("\t %d \t %f \t %f \t %f\n", i, waitTable[i], burstTable[i], waitTable[i] + burstTable[i]);
            }
            return;
        case 1:
            printf("\nFCFS started!");
            FCFSScheduler(core, processMemoryTable, processTable);
            printf("\nFCFS complete!");
            printf("\n------FCFS OUTPUT------\n");
            printf("\t PID \t WAIT TIME \t BURST TIME \t TURNAROUND TIME\n");
            for (int i=0; i<MAX_PROCESSES; i++){
                printf("\t %d \t %f \t %f \t %f\n", i, waitTable[i], burstTable[i], waitTable[i] + burstTable[i]);
            }
            return;
        case 2:
            printf("\nPriority started!");
            priorityScheduler(core, processMemoryTable, processTable);
            printf("\nPriority complete!");
            printf("\n------PRIORITY OUTPUT------\n");
            printf("\t PID \t WAIT TIME \t BURST TIME \t TURNAROUND TIME\n");
            for (int i=0; i<MAX_PROCESSES; i++){
                printf("\t %d \t %f \t %f \t %f\n", i, waitTable[i], burstTable[i], waitTable[i] + burstTable[i]);
            }
            return;
        case 3:
            printf("\nSRT started!");
            SRTScheduler(core, processMemoryTable, processTable);
            printf("\nSRT complete!");
            printf("\n------SRT OUTPUT------\n");
            printf("\t PID \t WAIT TIME \t BURST TIME \t TURNAROUND TIME\n");
            for (int i=0; i<MAX_PROCESSES; i++){
                printf("\t %d \t %f \t %f \t %f\n", i, waitTable[i], burstTable[i], waitTable[i] + burstTable[i]);
            }
            return;
        case 4:
            printf("\nHRRN started!");
            HRRNScheduler(core, processMemoryTable, processTable);
            printf("\nHRRN complete!");
            printf("\n------HRRN OUTPUT------\n");
            printf("\t PID \t WAIT TIME \t BURST TIME \t TURNAROUND TIME\n");
            for (int i=0; i<MAX_PROCESSES; i++){
                printf("\t %d \t %f \t %f \t %f\n", i, waitTable[i], burstTable[i], waitTable[i] + burstTable[i]);
            }
            return;
        case 5:
            printf("\nSPN started!");
            SPNScheduler(core, processMemoryTable, processTable);
            printf("\nSPN complete!");
            printf("\n------SPN OUTPUT------\n");
            printf("\t PID \t WAIT TIME \t BURST TIME \t TURNAROUND TIME\n");
            for (int i=0; i<MAX_PROCESSES; i++){
                printf("\t %d \t %f \t %f \t %f\n", i, waitTable[i], burstTable[i], waitTable[i] + burstTable[i]);
            }
            return;
        case 6:
            printf("\nFeedback started!");
            feedBackScheduler(core, processMemoryTable, processTable);
            printf("\nFeedback complete!");
            printf("\n------Feedback OUTPUT------\n");
            printf("\t PID \t WAIT TIME \t BURST TIME \t TURNAROUND TIME\n");
            for (int i=0; i<MAX_PROCESSES; i++){
                printf("\t %d \t %f \t %f \t %f\n", i, waitTable[i], burstTable[i], waitTable[i] + burstTable[i]);
            }
            return;
    }
}
// load all programs to memory
void loadProgram4() {
    // Complete: Load sample instructions into memory
    // Eg:
    // memory[0] = LOAD; memory[1] = 10; //LOAD 10 into ACC
    // Add more instructions as needed
    //  CORE 0
    accessMemory(2, LOAD, 1);
    accessMemory(3, 10, 1);  // LOAD 10 to ACC
    accessMemory(4, ADD, 1);
    accessMemory(5, 8, 1);  // ADD 8 to ACC
    accessMemory(6, STORE, 1);
    accessMemory(7, 15, 1);  // STORE ACC to 15
    accessMemory(8, LOAD, 1);
    accessMemory(9, 30, 1);  // LOAD 30 to ACC
    accessMemory(10, ADD, 1);
    accessMemory(11, 9, 1);  // ADD 9 to ACC
    accessMemory(12, STORE, 1);
    accessMemory(13, 19, 1);  // STORE ACC to 19
}
// main function
int main() {

    //initCoreMemoryTable();
    //initIVT();
    //loadProgram4();  // initialize memory with instructions
    /*for (int i=0; i<NUM_CORES; i++) {
      allocateMemory(i, 10);
    }*/
    //pthread_mutex_init(&interrupt_mutex, NULL);
    // create a thread to simulate interrupt generation
    //pthread_t interrupt_thread;
    //pthread_create(&interrupt_thread, NULL, generateInterrupts, NULL); ( /// UNCOMMENT TO TEST INTERRUPTS /// )
    // wait for the interrupt thread to complete
    //pthread_join(interrupt_thread, NULL);
    // clean up resources
    //pthread_mutex_destroy(&interrupt_mutex);
    // initialize mutex for memory access
    //pthread_mutex_init(&memory_mutex, NULL);
    initTables();
    time_t starttime, endtime;  // Use time_t for wall-clock time
    double runtimes[6]; 
    /*
    // create a thread for concurrent processing
    pthread_t cpu_thread[NUM_CORES];
    cpustart = clock();
    for (int i = 0; i < NUM_CORES; i++) {
        int* arg = malloc(sizeof(int));
        *arg = i;
        pthread_create(&cpu_thread[i], NULL, cpuCore, arg);
    }

    for (int i = 0; i < NUM_CORES; i++) {
        pthread_join(cpu_thread[i], NULL);
    }
    cpuend=clock();
    */
   //cpuCore4();

   for (int i=0;i<5;i++) {
        initCoreMemoryTable();
        initIVT();
        loadProgram4();
         starttime = time(NULL);       // Start timing (in seconds since epoch)
        cpuCore4(0);                   // Call the function
        endtime = time(NULL);         // End timing

        runtimes[i] = (double)(endtime-starttime);  // Calculate elapsed time in seconds
        printf("Run %d: %.2f seconds\n", i, runtimes[i]);
    }

    printf("\nRound Robin Runtime with TQ 3 = %f", runtimes[0]);
     printf("\nFCFS Runtime = %f", runtimes[1]);
     printf("\nPriority Runtime = %f", runtimes[2]);
    printf("\nSRT Runtime = %f", runtimes[3]);
    printf("\nHRRN Runtime = %f", runtimes[4]);
    printf("\nSPN Runtime = %f", runtimes[5]);
    printf("\nFeedback Runtime = %f", runtimes[6]);
    //printf("CPU Runtime: %d\n", cpuend-cpustart);
    //printf("Scheduler Runtime: %d\n", schedulerend-schedulerstart);
    //printf("Memory Allocation Runtime: %d\n", memend-memstart);

    //sem_init(&buffer_full, 0, 0);
    //sem_init(&buffer_empty, 0, BUFFER_SIZE);

    //pthread_t producer_thread, consumer_thread;
    //pthread_create(&producer_thread, NULL, producer, NULL);
    //pthread_create(&consumer_thread, NULL, consumer, NULL);

    //pthread_join(producer_thread, NULL);
   // pthread_join(consumer_thread, NULL);


    // clean up mutex

    //pthread_mutex_destroy(&memory_mutex);
    //pthread_mutex_destroy(&buffer_mutex);
    //sem_destroy(&buffer_full);
   // sem_destroy(&buffer_empty);

    //printf("\n\n%d", accessMemory(15, 0, 0));
   // printf("\n\n%d", accessMemory(421, 0, 0));
    //printf("\n0: %d 1: %d 2: %d 3: %d", ACC[0], ACC[1], ACC[2], ACC[3]);
    /*printf("\n Table 0: %d \n Table 1: %d \n Table 2: %d \n Table 3: %d \n Table Shared: %d",
           coreMemoryTable[0].memoryStart, coreMemoryTable[1].memoryStart,
           coreMemoryTable[2].memoryStart, coreMemoryTable[3].memoryStart,
           coreMemoryTable[4].memoryStart);*/

    return 0;
}
