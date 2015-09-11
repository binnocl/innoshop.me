var actions = Reflux.createActions([
    'addToBasket', 'decFromBasket'
]);

var ProductStore = Reflux.createStore({
    init: function() {
        this.data = [];
    },
    setInitialState: function(products) {
        this.data = products;
    },
    getInitialState: function() {
        return this.data;
    },
    getProduct: function(id) {
        return this.data[id];
    },
    add: function( product ) {
        this.data[product.id] = product;
    }
});

var BasketStore = Reflux.createStore({
    init: function() {
        this.data = [];
        this.listenTo(actions.addToBasket, this.onAddToBasket);
        this.listenTo(actions.decFromBasket, this.onDecFromBasket);
    },
    initialize: function(url, get_url){
        this.url = url;
        var self = this;
        $.get(get_url, function(res){
            res = JSON.parse(res);
            for(var i in res) {
                ProductStore.add(res[i].product);
                self.data[res[i].product.id] = res[i];
            }
            self.trigger( self.totalSum() );
        })
    },
    onDecFromBasket: function(id, remove){
        if( this.data[id] ) {
            var cnt = remove ? this.data[id].count : 1;
            this.data[id].count = this.data[id].count - cnt;
            if( this.data[id].count <= 0 )
                delete this.data[id];
            $.get( this.url + '?id=' + id + '&count=-' + cnt, function(res){  } );
            this.trigger( this.totalSum() );
        }
    },
    onAddToBasket: function(id) {
        if( this.data[id] ) {
            this.data[id].count = this.data[id].count + 1;
        }
        else {
            var product = ProductStore.getProduct(id);
            if( product ) this.data[id] = { count: 1, product: product};
        }
        $.get( this.url + '?id=' + id + '&count=1', function(res){  } );
        this.trigger( this.totalSum() );
    },
    totalSum: function() {
        var total = 0;
        for(var i in this.data)
            total += this.data[i].count * this.data[i].product.price;
        return total;
    },
    getInitialState: function() {
        return this.data;
    },
    get: function(id){
        return this.data[id];
    },
    items: function() {
        return this.data;
    },
    getProductCount: function(id) {
        return this.data[id] ? this.data[id].count : 0;
    }
});

var Price = React.createClass({
    mixins: [Reflux.listenTo(BasketStore, "onBasketChange")],
    onBasketChange: function(total) {
        this.setProps({ count: BasketStore.getProductCount(this.props.id) });
    },
    onClick: function() {
        actions.addToBasket(this.props.id);
    },
    render: function() {
        var button_class = "btn product__add ";
        button_class += this.props.count > 0 ? "btn-info" : "btn-default";
        var cnt = this.props.count > 0 ? ' [' + this.props.count + ']'  : '';
        return (
            <div className={button_class} onClick={this.onClick}>
                <span className="product__price">
                    <i style={ { lineHeight: '8px' } } className="fa fa-plus"></i>&nbsp;&nbsp;в карму</span>
                    {cnt}
            </div>
        );
    }
});

var Basket = React.createClass({
    mixins: [Reflux.listenTo(BasketStore, "onBasketChange")],
    onBasketChange: function(total) {
        this.setProps({ price: total });
    },
    onClick: function(event) {
        event.preventDefault();
        $('#basket-list').slideToggle();
    },
    render: function() {
        var has_price = this.props.price > 0;
        var basket_class = "btn btn" + (has_price ? '-success' : '-default');
        var price = has_price ? <span className="basket__price"> {this.props.price} <i className="fa fa-ruble"></i></span> : '';
        return (
                <a href={this.props.url} onClick={this.onClick} className="basket">
                    <span className={basket_class}>
                        <i className="fa fa-shopping-cart"></i> Карма
                        { price }
                    </span>
                </a>
        );
    }
});

var BasketLine = React.createClass({
    add: function() {
        actions.addToBasket(this.props.product.id);
    },
    dec: function() {
        actions.decFromBasket(this.props.product.id);
    },
    remove: function() {
        actions.decFromBasket(this.props.product.id, true);
    },
    render: function() {
        var sum = this.props.product.price * this.props.count;
        return (<tr>
                    <td width="1%">
                        <div className="btn  btn-default" onClick={this.add}><i className="fa fa-plus"></i></div>
                    </td>
                    <td width="1%">
                        <div className="btn  btn-default" onClick={this.dec}><i className="fa fa-minus"></i></div>
                    </td>
                    <td>
                        <span className="h4">{this.props.count}</span>
                    </td>
                    <td>
                        <span dangerouslySetInnerHTML={{__html: this.props.product.name}} />
                        <sup className="text-danger" style={ { whiteSpace: 'nowrap' } }> {this.props.product.price} <i className="fa fa-ruble"></i></sup>
                    </td>
                    <td className="h4 text-right">
                        {sum}&nbsp;<i className="fa fa-ruble" />
                    </td>
                </tr>
            )
    }
});

var BasketList = React.createClass({
    mixins: [Reflux.listenTo(BasketStore, "onBasketChange")],
    onBasketChange: function(total) {
        this.setProps({ items: BasketStore.items(), total: BasketStore.totalSum() });
    },
    render: function() {
        var self = this;
        var items = this.props.items;
        var list = items ?
            items.map( function( item ){ item.key = item.product.id; return (<BasketLine {...item} />); })
            : '';
        var btn = this.props.link ?
                    (<button type="submit" target="orderForm" className="btn btn-info" href={this.props.link} alt="Потратить карму">
                        <i className="fa fa-shopping-cart" />&nbsp;&nbsp;Потратить
                    </button>)
                    : '';

        var form = this.props.link ? (
            <div><br></br>
                <div className="form-group">
                    <input type="text" id="contact" name="contact" className="form-control"
                           placeholder="@telegram или номер телефона"></input>
                </div>
                <div className="form-group">
                    <textarea name="comment" id="comment" cols="30" rows="3" placeholder="Комментарий"
                              className="form-control" ></textarea>
                </div>
            </div>
        ) :'';
        var csrf = this.props.csrf_token ? (<input type="hidden" name="csrfmiddlewaretoken" value={this.props.csrf_token}></input>) : '';
        return (items || this.props.link) ? (
           <div className="basket-list">
                <form action={this.props.link} id="orderForm" method="POST">
                    {csrf}
                    <div className="panel panel-default">
                      <div className="panel-body">
                        <table><tbody>{list}</tbody></table>
                        {form}
                      </div>
                      <div className="panel-footer clearfix">
                        <span className="h3">Ваша карма {this.props.total} <i className="fa fa-ruble"></i></span>
                        <div className="pull-right product__add">{ btn }</div>
                      </div>
                    </div>
                </form>
           </div>
        ) : '';
    }
});