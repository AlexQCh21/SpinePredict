export default class View{
    constructor(){
        this.model = null;
        this.table = document.getElementById('tbl');
    }

    setModel(model){
        this.model=model;
    }
}