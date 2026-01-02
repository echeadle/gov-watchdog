#!/bin/bash
# Database management script for Gov Watchdog

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
MONGO_PASSWORD="${MONGO_PASSWORD:-devpassword}"
MONGO_HOST="${MONGO_HOST:-localhost}"
MONGO_PORT="${MONGO_PORT:-27017}"
DB_NAME="${DB_NAME:-gov_watchdog}"

show_help() {
    echo "Gov Watchdog Database Management"
    echo ""
    echo "Usage: ./scripts/db-manage.sh [command]"
    echo ""
    echo "Commands:"
    echo "  sync-members    Sync all current Congress members from Congress.gov"
    echo "  sync-house      Sync only House members"
    echo "  sync-senate     Sync only Senate members"
    echo "  stats           Show database statistics"
    echo "  shell           Open MongoDB shell"
    echo "  export          Export database to JSON files"
    echo "  import          Import database from JSON files"
    echo "  reset           Reset database (WARNING: deletes all data)"
    echo "  help            Show this help message"
    echo ""
}

sync_members() {
    echo -e "${GREEN}Syncing Congress members...${NC}"
    docker compose exec backend python manage.py sync_members "$@"
}

show_stats() {
    echo -e "${GREEN}Database Statistics${NC}"
    echo "-------------------"
    docker compose exec mongodb mongosh \
        "mongodb://admin:${MONGO_PASSWORD}@localhost:27017/${DB_NAME}?authSource=admin" \
        --quiet \
        --eval "
            print('Members: ' + db.members.countDocuments({}));
            print('Bills: ' + db.bills.countDocuments({}));
            print('Votes: ' + db.votes.countDocuments({}));
            print('');
            print('Members by party:');
            db.members.aggregate([
                {\$group: {_id: '\$party', count: {\$sum: 1}}},
                {\$sort: {count: -1}}
            ]).forEach(doc => print('  ' + doc._id + ': ' + doc.count));
            print('');
            print('Members by chamber:');
            db.members.aggregate([
                {\$group: {_id: '\$chamber', count: {\$sum: 1}}},
                {\$sort: {count: -1}}
            ]).forEach(doc => print('  ' + doc._id + ': ' + doc.count));
        "
}

open_shell() {
    echo -e "${GREEN}Opening MongoDB shell...${NC}"
    docker compose exec mongodb mongosh \
        "mongodb://admin:${MONGO_PASSWORD}@localhost:27017/${DB_NAME}?authSource=admin"
}

export_db() {
    EXPORT_DIR="./data/exports/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$EXPORT_DIR"

    echo -e "${GREEN}Exporting database to ${EXPORT_DIR}...${NC}"

    for collection in members bills votes; do
        echo "Exporting $collection..."
        docker compose exec mongodb mongoexport \
            --uri="mongodb://admin:${MONGO_PASSWORD}@localhost:27017/${DB_NAME}?authSource=admin" \
            --collection="$collection" \
            --out="/tmp/${collection}.json"
        docker compose cp "mongodb:/tmp/${collection}.json" "$EXPORT_DIR/${collection}.json"
    done

    echo -e "${GREEN}Export complete: ${EXPORT_DIR}${NC}"
}

import_db() {
    if [ -z "$1" ]; then
        echo -e "${RED}Please specify the export directory to import from${NC}"
        echo "Usage: ./scripts/db-manage.sh import ./data/exports/20240101_120000"
        exit 1
    fi

    IMPORT_DIR="$1"

    if [ ! -d "$IMPORT_DIR" ]; then
        echo -e "${RED}Directory not found: ${IMPORT_DIR}${NC}"
        exit 1
    fi

    echo -e "${YELLOW}This will replace existing data. Continue? (y/N)${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi

    echo -e "${GREEN}Importing database from ${IMPORT_DIR}...${NC}"

    for collection in members bills votes; do
        if [ -f "$IMPORT_DIR/${collection}.json" ]; then
            echo "Importing $collection..."
            docker compose cp "$IMPORT_DIR/${collection}.json" "mongodb:/tmp/${collection}.json"
            docker compose exec mongodb mongoimport \
                --uri="mongodb://admin:${MONGO_PASSWORD}@localhost:27017/${DB_NAME}?authSource=admin" \
                --collection="$collection" \
                --file="/tmp/${collection}.json" \
                --drop
        fi
    done

    echo -e "${GREEN}Import complete${NC}"
}

reset_db() {
    echo -e "${RED}WARNING: This will delete ALL data in the database!${NC}"
    echo -e "${YELLOW}Type 'yes' to confirm:${NC}"
    read -r response
    if [ "$response" != "yes" ]; then
        echo "Cancelled."
        exit 0
    fi

    echo -e "${GREEN}Resetting database...${NC}"
    docker compose exec mongodb mongosh \
        "mongodb://admin:${MONGO_PASSWORD}@localhost:27017/${DB_NAME}?authSource=admin" \
        --quiet \
        --eval "
            db.members.drop();
            db.bills.drop();
            db.votes.drop();
            print('Database reset complete');
        "

    # Re-run init script
    docker compose exec mongodb mongosh \
        "mongodb://admin:${MONGO_PASSWORD}@localhost:27017/admin" \
        --quiet \
        /docker-entrypoint-initdb.d/mongo-init.js

    echo -e "${GREEN}Database reset and reinitialized${NC}"
}

# Main command handler
case "$1" in
    sync-members)
        sync_members
        ;;
    sync-house)
        sync_members --chamber house
        ;;
    sync-senate)
        sync_members --chamber senate
        ;;
    stats)
        show_stats
        ;;
    shell)
        open_shell
        ;;
    export)
        export_db
        ;;
    import)
        import_db "$2"
        ;;
    reset)
        reset_db
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac
