# routes/home.py
from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from controllers.user_controller import update_profile, get_user_profile
from controllers.business_controller import get_all_businesses, get_business_by_id
from models.user import User
from models.business import Business
from patterns.factory_category import CategoryFactory
from models.business import Service

# How many categories to show on the home page
MAX_CATEGORIES_DISPLAY = 5

home_bp = Blueprint('home', __name__, template_folder='../../frontend')

@home_bp.route('/')
@home_bp.route('/home')
def index():
    """Home page - landing page with categories and popular businesses"""
    # Get categories from factory (limit to most important ones)
    categories = CategoryFactory.get_all_categories()[:MAX_CATEGORIES_DISPLAY]
    
    # Get popular/recent businesses (limit to 6 for homepage)
    businesses = get_all_businesses()
    popular_businesses = businesses[:6] if businesses else []
    
    return render_template('Home/landing.html',
                         categories=categories,
                         popular_businesses=popular_businesses)
@home_bp.route('/category/')
def category_root():
    """Redirect bare `/category/` requests back to home to avoid 404s."""
    return redirect(url_for('home.index'))


@home_bp.route('/services')
def services_list():
    """Browse all businesses with search and filter options"""
    # Get filter parameters
    category = request.args.get('category', '')
    city = request.args.get('city', '')
    search_query = request.args.get('q', '')
    
    # Get all businesses
    all_businesses = get_all_businesses()
    
    # Apply filters
    filtered_businesses = all_businesses
    
    if category:
        filtered_businesses = [b for b in filtered_businesses if b.category == category]
    
    if city:
        filtered_businesses = [b for b in filtered_businesses if b.city.lower() == city.lower()]
    
    if search_query:
        query_lower = search_query.lower()
        filtered_businesses = [
            b for b in filtered_businesses 
            if query_lower in b.name.lower() 
            or query_lower in b.description.lower() if b.description else False
            or query_lower in b.city.lower()
            or query_lower in b.district.lower()
        ]
    
    # Get all categories for filter dropdown
    categories = CategoryFactory.get_all_categories()
    
    # Get unique cities for filter dropdown
    cities = sorted(list(set(b.city for b in all_businesses)))
    
    return render_template('services.html',
                         businesses=filtered_businesses,
                         categories=categories,
                         cities=cities,
                         selected_category=category,
                         selected_city=city,
                         search_query=search_query)
@home_bp.route('/category/<category_id>')
def category_list(category_id):
    """Show all businesses in a specific category"""
    category = CategoryFactory.get_category(category_id)
    
    if not category:
        flash('Category not found', 'danger')
        return redirect(url_for('home.index'))
    
    # Filter businesses by category (match against category.name which is the ID)
    all_businesses = get_all_businesses()
    filtered_businesses = [b for b in all_businesses if b.category == category_id]
    
    return render_template('category_list.html',
                         category_name=category.display_name,
                         businesses=filtered_businesses)


@home_bp.route('/my-bookings')
@login_required
def my_bookings():
    """Show user's bookings with active and completed tabs"""
    from controllers.booking_controller import get_user_bookings
    
    bookings = get_user_bookings(current_user.user_id)
    
    # Separate into active and completed
    active_bookings = [b for b in bookings if b.status in ['pending', 'accepted']]
    completed_bookings = [b for b in bookings if b.status in ['completed', 'cancelled', 'rejected']]
    
    return render_template('my_bookings.html',
                         active_bookings=active_bookings,
                         completed_bookings=completed_bookings)


@home_bp.route('/search')
def search():
    """Search for businesses and services"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return redirect(url_for('home.index'))
    
    # Search in businesses and categories
    all_businesses = get_all_businesses()
    
    # Simple text search in business name, category, and fields
    results = []
    for b in all_businesses:
        search_fields = [
            b.name.lower(),
            b.category.lower(),
            b.city.lower(),
            b.district.lower(),
            b.description.lower() if b.description else ''
        ]
        if any(query.lower() in field for field in search_fields):
            results.append(b)
    
    return render_template('category_list.html',
                         category_name=f'Search Results for "{query}"',
                         businesses=results)


@home_bp.route('/dashboard')
def dashboard():
    """Dashboard - requires login"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
   
    user_name = session.get('user_name')
    return render_template('dashboard.html', user_name=user_name)


@home_bp.route('/profile', methods=['GET'])
@login_required
def profile():
    """View user profile with optimized lazy-loaded images"""
    # Use Flask-Login's current_user
    user_data = get_user_profile(current_user.user_id, thumbnail_size=150)
    if not user_data:
        flash('User not found', 'danger')
        return redirect(url_for('home.index'))
    
    return render_template('profile.html', user=user_data)


@home_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile_route():
    """Update user profile with optional profile picture upload"""
    user_id = current_user.user_id
    
    # Get form data
    data = {
        'name': request.form.get('name'),
        'phone': request.form.get('phone'),
        'street_house': request.form.get('street_house'),
        'city': request.form.get('city'),
        'district': request.form.get('district')
    }
    
    # Get profile picture file if uploaded
    profile_picture = request.files.get('profile_picture')
    
    # Update profile with Cloudinary upload
    user, error = update_profile(user_id, data, profile_picture)
    
    if error:
        flash(error, 'danger')
    else:
        # Update session with new name if changed
        if data.get('name'):
            session['user_name'] = user.name
        flash('Profile updated successfully!', 'success')
    
    return redirect(url_for('home.profile'))


@home_bp.route('/about')
def about():
    """About Us page"""
    return render_template('about.html')