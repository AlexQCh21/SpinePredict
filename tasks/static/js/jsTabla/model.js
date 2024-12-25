export default class Model{

    constructor(){
        this.model = null;
        this.view = null;
        this.todo = [];
        
    }

    setModel(model){
        this.model=model;
    }

    setView(view){
        this.view = view;
    }
}