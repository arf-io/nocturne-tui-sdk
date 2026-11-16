#include "internal.h"
/* Direct and retained expressions share one bounded grammar and evaluator. */
int nrNumericExpression(const State*s,const Json*j,int at,int intentAt,double*out){
    const Intent*intent=0;
    if(intentAt>=0){double value;if(!nrNumber(j,intentAt,&value)||value<1||value>9007199254740991.0||value!=(uint64_t)value)return 0;
        for(int i=0;i<NR_INTENTS;i++)if(s->intents[i].used&&s->intents[i].id==(uint64_t)value)intent=&s->intents[i];
        if(!intent)return 0;
    }
    NumericFormula formula;
    if(!nrCompileTriggerFormula(s,j,at,&formula))return 0;
    double values[NR_VALUES];for(int i=0;i<NR_VALUES;i++)values[i]=s->values[i].value;
    return nrEvalTriggerFormula(&formula,values,intent,intent?&s->intentPayloads[intent-s->intents]:0,out);
}

/* Future data availability is not snapshot integrity. Only dependency-bearing
 * expressions use this import-only structural path; literal expressions still
 * receive normal output type/range/binding validation. */
int nrPendingExpressionShape(NrContext*c,const State*s,const Json*j,int at,int intentAt){
    if(!c->checkingPending||s!=&c->probe)return 0;
    if(intentAt>=0){double id;if(!nrNumber(j,intentAt,&id)||id<1||id>9007199254740991.0||id!=(uint64_t)id)return 0;}
    if(!nrCompileDataFormula(s,j,at,&c->dataFormulaScratch))return 0;
    const NumericFormula*f=&c->dataFormulaScratch.tree;
    if(f->usesIntent)return intentAt>=0;
    for(int i=0;i<f->count;i++)if(f->nodes[i].kind==1||f->nodes[i].kind==11||f->nodes[i].kind==101)return 1;
    return 0;
}
