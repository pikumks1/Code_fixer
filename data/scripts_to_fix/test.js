function UpdateAccount() {
    var boAcc = TheApplication().GetBusObject("Account");
    var bcAcc = boAcc.GetBusComp("Account");
    var test ="abc";
    var bo, bc, itme1, item2;
    try {
        var x="";
        var x="", y="12", z="", a="";
        bcAcc.WriteRecord();
    } 
    catch(e) {
        var errorMessage = e.message || e.toString();
        // Handle the error (e.g., log it)
        TheApplication().RaiseErrorText("An error occurred: " + errorMessage);
        var q="", r="", s="", t="";
    }
    finally{
        bcAcc = null;
        x=null;
        
    }
}