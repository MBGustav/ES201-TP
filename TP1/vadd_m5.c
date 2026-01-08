#include <stdint.h>
#include "m5ops.h"
#define N 50

int main(void){
    volatile int a[N], b[N], c[N];

    m5_reset_stats(0, 0);

    for(int i=0;i<N;i++)
        c[i]=a[i]+b[i];

    m5_dump_stats(0, 0);
    return 0;
}
