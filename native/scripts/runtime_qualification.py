"""Runtime-plan status is narrower than final source and distribution qualification."""

def runtimePlanQualified(*,complete,sourceUnchanged,strict,capture,expectedCaseIds,commands,fourRuntimePassed):
    if any(value is not True for value in (complete,sourceUnchanged,strict,capture,fourRuntimePassed)):
        return False
    if not expectedCaseIds or len(set(expectedCaseIds))!=len(expectedCaseIds):return False
    if [row.get('id') for row in commands]!=expectedCaseIds:return False
    return all(row.get('status')=='PASS' and type(row.get('exitCode')) is int and row['exitCode']==0 for row in commands)
