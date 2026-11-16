#include "internal.h"
#include <stdio.h>
int main(void) {
 printf("{\"deposit\":%zu,\"depositSize\":%zu,\"id\":%zu,\"owner\":%zu,\"generation\":%zu,\"particle\":%zu,\"particleSize\":%zu,\"particleId\":%zu,\"nextParticle\":%zu,\"nextGeneration\":%zu}\n",offsetof(State,deposits),sizeof(Deposit),offsetof(Deposit,id),offsetof(Deposit,emitterId),offsetof(Deposit,emitterGeneration),offsetof(State,particles),sizeof(Particle),offsetof(Particle,id),offsetof(State,nextParticle),offsetof(State,nextEmitterGeneration));
}
