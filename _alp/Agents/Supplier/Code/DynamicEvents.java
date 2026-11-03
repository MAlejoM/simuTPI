void DeliverOrder(ProductType producto,double cantidad)
{/*ALCODESTART::1788974335148*/
send(new DeliveryMessage(producto, cantidad), ((Main)get_Main()).domitecPlant);
/*ALCODEEND*/}

