import decimal

subtotal = decimal.Decimal(str(default_to(field.subtotal, 0))) 
calculated_total = subtotal + \
               decimal.Decimal(str(default_to(field.misc_charges_export, 0))) + \
               decimal.Decimal(str(default_to(field.freight_export, 0))) + \
               decimal.Decimal(str(default_to(field.dropship_freight_export, 0))) + \
               decimal.Decimal(str(default_to(field.merchant_tax_export, 0))) + \
               decimal.Decimal(str(default_to(field.retention_tax_export, 0))) + \
               decimal.Decimal(str(default_to(field.plate_charge_export, 0))) + \
               decimal.Decimal(str(default_to(field.pallet_charge_export, 0))) - \
               decimal.Decimal(str(abs(default_to(field.trade_discount, 0)))) - \
               decimal.Decimal(str(abs(default_to(field.purchase_discount_export, 0)))) - \
               decimal.Decimal(str(abs(default_to(field.backhaul_allowance_export, 0)))) - \
               decimal.Decimal(str(abs(default_to(field.rebate_export, 0))))
               
calculated_total