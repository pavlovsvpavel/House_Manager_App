from house_manager.houses.models import HouseCalculationsOptions


def handle_client(current_client):
    if current_client.is_inhabitable:
        return True
    return False


def handle_not_used_fields(current_field):
    if current_field in ['id', 'total_amount', 'client', 'house', 'user', 'signature', 'type_of_bill']:
        return True
    return False


def handle_text_fields(current_field):
    if current_field in ['month', 'year', 'comment']:
        return True
    return False


def handle_calculation_options(house_id, user_id):
    try:
        calc_options = HouseCalculationsOptions.objects.get(
            house_id=house_id,
            user_id=user_id
        )

        return (
            calc_options.based_on_apartment,
            calc_options.based_on_total_people
        )
    except HouseCalculationsOptions.DoesNotExist as error:
        raise error
