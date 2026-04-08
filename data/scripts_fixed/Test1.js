function UpdateAccount() {
    try {
        var boAcc = TheApplication().GetBusObject("Account");
    var bcAcc = boAcc.GetBusComp("Account");
    var test ="abc";
    var bo, bc, itme1, item2;
    } catch(e) {
        throw e;
    } finally {
        if(defined(bcAcc)) bcAcc = null;
        if(defined(boAcc)) boAcc = null;
        if(defined(test)) test = null;
        if(defined(bo)) bo = null;
        if(defined(bc)) bc = null;
        if(defined(itme1)) itme1 = null;
        if(defined(item2)) item2 = null;
    }
}